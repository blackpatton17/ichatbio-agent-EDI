import os
from typing import Optional, Literal, AsyncGenerator, Dict, List, Union
from typing_extensions import override
from urllib.parse import urlencode
from pathlib import Path

import dotenv
import instructor
import requests
import json
import xml.etree.ElementTree as ET
from openai import AsyncOpenAI
from pydantic import Field, BaseModel
from tenacity import AsyncRetrying

from instructor import AsyncInstructor
from instructor.exceptions import InstructorRetryException

from util.ai import StopOnTerminalErrorOrMaxAttempts, AIGenerationException
from ichatbio.agent import IChatBioAgent
from ichatbio.types import AgentCard, AgentEntrypoint
from ichatbio.agent_response import ResponseContext

dotenv.load_dotenv()

EDIResponseFormat = Literal["png", "json"]


class EDIAgent(IChatBioAgent):
    def __init__(self):
        self.agent_card = AgentCard(
            name="EDI Dataset Agent",
            description="Searches datasets from PASTA+ EDI repository.",
            icon=None,
            entrypoints=[
                AgentEntrypoint(
                    id="search_dataset",
                    description="Searches EDI for datasets using metadata or keyword search.",
                    parameters=None,
		        )
            ]
        )

    @override
    def get_agent_card(self) -> AgentCard:
        return self.agent_card

    @override
    async def run(self, request: str, entrypoint: str, params: Optional[BaseModel]):
        async with context.begin_process(summary="Generating EDI query") as process:
            simple_params, description = await _generate_records_search_parameters(request)
            edi_query = EDIQueryModel(**simple_params.model_dump())
            url = edi_query.to_url()

            await process.log(f"Using structured parameters to query EDI, url: {url}")

            await process.log(f"Sending GET request to {url}")
            response = await self._fetch_edi_data(url)

            if response.status_code != 200:
                raise AIGenerationException(f"Failed to fetch data from EDI: {response.status_code} {response.text}")
                return
            results = response.text.strip()
            
            if not results:
                await process.log("No datasets matched your query.")
                return
            
            await process.log("Datasets found, processing results...")
            root = ET.fromstring(results)
            entries = []
            for doc in root.findall("document")[:10]:
                entry = {}
                for child in doc:
                    # If the child has sub-elements, handle as list or dict
                    if list(child):
                        # If all sub-elements are <keyword>, collect as list
                        if all(grandchild.tag == "keyword" for grandchild in child):
                            entry[child.tag] = [kw.text for kw in child.findall("keyword")]
                        else:
                            # For other nested structures, store as dict
                            entry[child.tag] = {grandchild.tag: grandchild.text for grandchild in child}
                    else:
                        entry[child.tag] = child.text
                # Add a URL field if packageid exists
                if "packageid" in entry:
                    # Convert packageid from "scope.id.revision" to "scope/id/revision"
                    scope, id_, revision = entry["packageid"].split(".")
                    entry["url"] = f"https://pasta.lternet.edu/package/metadata/eml/{scope}/{id_}/{revision}"
                entries.append(entry)

            await context.reply(
                "Results saved locally"
                # description=f"Saved the top 10 datasets to {output_path.resolve()}",
                # data={"output_path": str(output_path.resolve())}
            )

            await process.create_artifact(
                mimetype="application/json",
                description=f"Here are the top 10 matching datasets from {url}",
                content=json.dumps({"datasets": entries}).encode("utf-8")
            )
            # Save the entries to a local JSON file
            # output_path = Path(os.getenv("EDI_RESULTS_PATH", "edi_search_results.json"))
            # with output_path.open("w", encoding="utf-8") as f:
            #     json.dump({"datasets": entries}, f, ensure_ascii=False, indent=2)


class SimpleFilterField(BaseModel):
    type: Literal["exact", "fulltext", "range", "prefix"]
    value: Union[str, dict]


class SimplePASTAQuery(BaseModel):
    q: Optional[Dict[str, Dict[str, Literal["existed", "missing", "prefix"]]]] = Field(default_factory=dict)
    fq: Optional[Dict[str, SimpleFilterField]] = Field(default_factory=dict)
    fl: Optional[List[str]] = Field(default_factory=list)
    rows: Optional[int] = Field(default=1000)
    start: Optional[int] = Field(default=0)
    sort: Optional[str] = None

class EDIQueryModel(SimplePASTAQuery):
    def to_url(self) -> str:
        base_url = "https://pasta.lternet.edu/package/search/eml"
        params = {}

        q_clauses = []
        intent_map = {
            "existed": "{field}{term}",
            "missing": "-{field}{term}",
            "prefix": "{field}{term}*",
        }

        for field_name, terms in self.q.items():
            for term, intent in terms.items():
                # Quote term if it contains spaces
                quoted_term = f"\"{term}\"" if " " in term else term
                # Compute the field part of the clause
                field = f"{field_name}:" if field_name != "uncategorized" else ""
                # Append using the appropriate pattern
                q_clauses.append(intent_map[intent].format(field=field, term=quoted_term))

        params["q"] = "+".join(q_clauses) if q_clauses else "*"

        fq_list = []
        for field, filter_obj in self.fq.items():
            if filter_obj.type == "range":
                val = filter_obj.value
                if hasattr(val, "gte") and hasattr(val, "lte"):
                    fq_list.append(f"{field}:[{val.gte} TO {val.lte}]")
                elif isinstance(val, dict):
                    top = val['left_top']
                    bottom = val['right_bottom']
                    fq_list.append(f"{field}:[{top['lat']},{top['lon']} TO {bottom['lat']},{bottom['lon']}]")
            else:
                fq_list.append(f"{field}:{filter_obj.value}")
        if fq_list:
            params["fq"] = fq_list

        if self.fl:
            params["fl"] = ",".join(self.fl)
        if self.rows:
            params["rows"] = str(self.rows)
        if self.start:
            params["start"] = str(self.start)
        if self.sort:
            params["sort"] = self.sort

        query_parts = []
        for param_key, param_value in params.items():
            if isinstance(param_value, list):
                for item in param_value:
                    query_parts.append(f"{param_key}={item}")
            else:
                query_parts.append(f"{param_key}={param_value}")
        return f"{base_url}?" + "&".join(query_parts)



class LLMResponseModel(BaseModel):
    plan: str = Field(description="A brief explanation of what API parameters you plan to use")
    search_parameters: SimplePASTAQuery = Field()
    artifact_description: str = Field(description="A concise characterization of the retrieved occurrence record data")


async def _generate_records_search_parameters(request: str) -> (SimplePASTAQuery, str):
    client: AsyncInstructor = instructor.from_openai(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

    try:
        result = await client.chat.completions.create(
            model="gpt-4.1",
            temperature=0,
            response_model=LLMResponseModel,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": request}
            ],
        )
    except InstructorRetryException as e:
        raise AIGenerationException(e)

    return result.search_parameters, result.artifact_description

async def _generate_records_summary(artifact: dict) -> str:
    """Generate a summary of the EDI dataset artifact."""
    client: AsyncInstructor = instructor.from_openai(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

    try:
        result = await client.chat.completions.create(
            model="gpt-4.1",
            temperature=0,
            response_model=LLMResponseModel,
            messages=[
                {"role": "system", "content": "You summarize EDI dataset artifacts."},
                {"role": "user", "content": json.dumps(artifact)},
            ],
        )
    except InstructorRetryException as e:
        raise AIGenerationException(e)

    return result.search_parameters, result.artifact_description


SYSTEM_PROMPT_TEMPLATE = """
You translate user requests into parameters for the iDigBio record search API.

# Query format

Here is a description of how iDigBio queries are formatted:

[BEGIN QUERY FORMAT DOC]

{query_format_doc}

[END QUERY FORMAT DOC]

# Examples

{examples_doc}
"""

def get_system_prompt():
    base = Path(__file__).parent / "resources"
    query_format_doc = (base / "records_query_format.md").read_text(encoding="utf-8")
    examples_doc = (base / "records_examples.md").read_text(encoding="utf-8")

    return SYSTEM_PROMPT_TEMPLATE.format(
        query_format_doc=query_format_doc,
        examples_doc=examples_doc
    ).strip()

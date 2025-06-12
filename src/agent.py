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
from ichatbio.types import AgentCard, AgentEntrypoint, ProcessMessage, TextMessage, ArtifactMessage, Message
from schema import PASTAQuery

dotenv.load_dotenv()

EDIResponseFormat = Literal["png", "json"]


class EDIAgent(IChatBioAgent):
    def __init__(self):
        self.agent_card = AgentCard(
            name="EDI Dataset Agent",
            description="Searches datasets from PASTA+ EDI repository.",
            entrypoints=[
                AgentEntrypoint(
                    id="search_dataset",
                    description="Searches EDI for datasets using metadata or keyword search.",
                    parameters=None
                )
            ]
        )

    @override
    def get_agent_card(self) -> AgentCard:
        return self.agent_card

    @override
    async def run(self, request: str, entrypoint: str, params: Optional[BaseModel]) -> AsyncGenerator[Message, None]:
        try:
            yield ProcessMessage(summary="Generating EDI query", description="Parsing user intent")

            simple_params, description = await _generate_records_search_parameters(request)
            edi_query = EDIQueryModel(**simple_params.model_dump())
            url = edi_query.to_url()

            yield ProcessMessage(
                summary="Query constructed",
                description=f"Using structured parameters to query EDI, url: {url}",
                data={"search_parameters": edi_query.model_dump(exclude_none=True)}
            )

            yield ProcessMessage(description=f"Sending GET request to {url}")
            response = requests.get(url)

            if response.status_code != 200:
                yield TextMessage(text=f"Query failed with status code {response.status_code}")
                return

            results = response.text.strip()
            if not results:
                yield TextMessage(text="No datasets matched your query.")
            else:
                root = ET.fromstring(results)
                entries = []
                for doc in root.findall("document")[:10]:
                    packageid = doc.findtext("packageid")
                    keywords = [kw.text for kw in doc.findall("keywords/keyword")]
                    title = doc.findtext("title")
                    entries.append({
                        "packageid": packageid,
                        "title": title,
                        "keywords": keywords
                    })

                yield ArtifactMessage(
                    mimetype="application/json",
                    description=f"Here are the top 10 matching datasets from {url}",
                    content=json.dumps({"datasets": entries}).encode("utf-8")
                )

        except InstructorRetryException:
            yield TextMessage(text="Sorry, I couldn't find any dataset.")


class EDIQueryModel(PASTAQuery):
    def to_url(self) -> str:
        base_url = "https://pasta.lternet.edu/package/search/eml"
        params = {}

        q_clauses = []
        for field, terms in self.q.items():
            for term, intent in terms.root.items():
                if intent == "existed":
                    q_clauses.append(f"{field}:{term}")
                elif intent == "missing":
                    q_clauses.append(f"-{field}:{term}")
                elif intent == "prefix":
                    q_clauses.append(f"{field}:{term}*")
        params["q"] = " AND ".join(q_clauses) if q_clauses else "*"

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

        return f"{base_url}?{urlencode(params, doseq=True)}"


class SimpleFilterField(BaseModel):
    type: Literal["exact", "fulltext", "range", "prefix"]
    value: Union[str, dict]


class SimplePASTAQuery(BaseModel):
    q: Optional[Dict[str, Dict[str, Literal["existed", "missing", "prefix"]]]] = Field(default_factory=dict)
    fq: Optional[Dict[str, SimpleFilterField]] = Field(default_factory=dict)
    fl: Optional[List[str]] = Field(default_factory=list)
    rows: Optional[int] = Field(default=10)
    start: Optional[int] = Field(default=0)
    sort: Optional[str] = None


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

import importlib.resources

import instructor
from instructor import AsyncInstructor
from instructor.exceptions import InstructorRetryException
from openai import AsyncOpenAI
from pydantic import Field, BaseModel
from tenacity import AsyncRetrying

import requests
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint
# from ..schema import IDigBioRecordsApiParameters
# from ..util import ai

from schema import EDIQueryModel, PASTAQuery, LLMResponseModel
from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts


entrypoint = AgentEntrypoint(
    id="search_dataset",
    description="Searches EDI for datasets using metadata or keyword search.",
    parameters=None,
)

async def run(self, context: ResponseContext, request: str):
    async with context.begin_process(summary="Generating EDI query") as process:
        params, description = await _generate_records_search_parameters(request)
        edi_query = EDIQueryModel(**params.model_dump())
        url = edi_query.to_url()

        await process.log(f"Using structured parameters to query EDI, url: {url}")

        await process.log(f"Sending GET request to {url}")
        response = await _fetch_edi_data(url)

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

async def _fetch_edi_data(url: str) -> requests.Response:
    """
    Fetch data from the EDI repository using the provided URL.
    This function uses a retry mechanism to handle transient errors.
    """
    async for attempt in AsyncRetrying(
        stop=StopOnTerminalErrorOrMaxAttempts(max_attempts=3),
        reraise=True,
        retry_error_cls=AIGenerationException
    ):
        with attempt:
            response = requests.get(url)
            if response.status_code != 200:
                raise AIGenerationException(f"Failed to fetch data from EDI: {response.status_code} {response.text}")
            return response


async def _generate_records_search_parameters(request: str) -> (PASTAQuery, str):
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
    query_format_doc = importlib.resources.files("resources").joinpath("records_query_format.md").read_text(encoding="utf-8")
    examples_doc = importlib.resources.files("resources").joinpath("records_examples.md").read_text(encoding="utf-8")

    return SYSTEM_PROMPT_TEMPLATE.format(
        query_format_doc=query_format_doc,
        examples_doc=examples_doc
    ).strip()

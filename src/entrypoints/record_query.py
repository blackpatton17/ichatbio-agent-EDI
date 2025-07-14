import importlib.resources

import instructor
from instructor import AsyncInstructor
from instructor.exceptions import InstructorRetryException
from openai import AsyncOpenAI, Client
from pydantic import Field, BaseModel
from tenacity import AsyncRetrying

import requests
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from io import TextIOWrapper

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint
# from ..schema import IDigBioRecordsApiParameters
# from ..util import ai

from schema import EDIQueryModel, PASTAQuery, LLMQueryParamResponseModel, LLMSummarizationResponseModel
from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts
import json
import re


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
        for doc in root.findall("document")[:5]:
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
        await process.log("Top 5 datasets formatted in JSON format.")

        await process.log("About to create artifact with dataset JSON")
        await process.create_artifact(
            mimetype="application/json",
            description=f"Here are the top 5 matching datasets from {url}",
            content=json.dumps({"datasets": entries}).encode("utf-8"),
            metadata={"api_query_url": url}
        )
        await process.log("Artifact created successfully")

        await context.reply(
            f"Results found at URL: {url}",
            # description=f"Saved the top 5 datasets to {output_path.resolve()}",
            # data={"output_path": str(output_path.resolve())}
        )

        # # Save the entries to a local JSON file
        # output_path = Path(os.getenv("EDI_RESULTS_PATH", "edi_search_results.json"))
        # # Write the file in text mode first (if needed), then reopen in binary mode for upload
        # json.dump({"datasets": entries}, output_path.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)
        # print("-" * 20)
        # summary_result = await _generate_records_summary(entries)
        # print(summary_result)
        # print("-" * 20)

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
    # Use custom endpoint and token if provided, else fallback to OpenAI defaults
    # api_key = os.getenv("GITHUB_PLAYGROUND_KEY")
    # base_url = "https://models.github.ai/inference"

    # client: AsyncInstructor = instructor.from_openai(
    #     AsyncOpenAI(api_key=api_key, base_url=base_url)
    # )
    api_key = os.getenv("OPENAI_API_KEY")
    client: AsyncOpenAI = instructor.from_openai(
        AsyncOpenAI(api_key=api_key)
    )

    try:
        result = await client.chat.completions.create(
            model="gpt-4.1",
            temperature=0,
            response_model=LLMQueryParamResponseModel,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": request}
            ],
        )
    except InstructorRetryException as e:
        raise AIGenerationException(e)

    return result.search_parameters, result.artifact_description

async def _generate_records_summary(entries: list) -> list[LLMSummarizationResponseModel]:
    """Generate a summary of the EDI dataset artifact."""

    # Use OpenAI API key for file upload and chat completion
    # api_key = os.getenv("GITHUB_PLAYGROUND_KEY")
    # base_url = "https://models.github.ai/inference"

    # client: AsyncInstructor = instructor.from_openai(
    #     AsyncOpenAI(api_key=api_key, base_url=base_url)
    # )

    api_key = os.getenv("OPENAI_API_KEY")
    client: AsyncOpenAI = instructor.from_openai(
        AsyncOpenAI(api_key=api_key)
    )

    summaries = []
    chunk_size = 1  # Number of datasets per chunk
    for i in range(0, len(entries), chunk_size):
        chunk = entries[i:i+chunk_size]
        chunk_content = json.dumps(chunk, ensure_ascii=False, indent=2)
        def clean_methods(text: str) -> str:
            lines = text.splitlines()
            cleaned = []

            for line in lines:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip lat/lon and numeric-only lines
                if re.match(r"^-?\d{2,3}\.\d+", line):
                    continue
                if re.match(r"^\d{3,4}$", line):
                    continue
                if line.lower() in {"meter", "meters"}:
                    continue

                # Skip location/elevation metadata
                if re.search(r"(elevation|gage|junction|tributary|creek|confluence|station)", line, re.IGNORECASE):
                    if len(line.split()) < 10:  # keep long sentences
                        continue

                cleaned.append(line)

            return "\n".join(cleaned)

        # Clean the 'methods' field in each dataset entry, if present
        for entry in chunk:
            if "methods" in entry and isinstance(entry["methods"], str):
                entry["methods"] = clean_methods(entry["methods"])
        try:
            result = await client.chat.completions.create(
                model="gpt-4.1",
                temperature=0,
                response_model=LLMSummarizationResponseModel,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": (
                            "The following is a JSON list of EDI dataset metadata. "
                            "Each dataset includes fields like title, abstract, and methods. "
                            "Please summarize each dataset in 3-5 sentences, focusing on title, abstract, and any available methods.\n\n"
                            f"{chunk_content}"
                        ),
                    }
                ],
            )
            print(f"Generated summary for chunk {i // chunk_size + 1}: {result.summary}")
            summaries.append(result)
        except InstructorRetryException as e:
            print(f"Failed to generate summary for chunk {i // chunk_size + 1}: {e}")
            # Print the 'methods' field of each entry in the chunk
            for entry in chunk:
                if "methods" in entry:
                    with open("failed_methods.json", "a", encoding="utf-8") as f:
                        json.dump({"methods": entry["methods"]}, f, ensure_ascii=False)
                        f.write("\n")
                    print("Methods:", entry["methods"])
            continue  # Skip this chunk and continue with the next
    return summaries

SYSTEM_PROMPT_TEMPLATE = """
You translate user requests into parameters for the EDIrecord search API.

# Query format

Here is a description of how EDIqueries are formatted:

[BEGIN QUERY FORMAT DOC]

{query_format_doc}

[END QUERY FORMAT DOC]

# Examples

{examples_doc}
"""

def get_system_prompt():
    query_format_doc = importlib.resources.files("resources").joinpath("records_query_format.md").read_text(encoding="utf-8")
    examples_doc = importlib.resources.files("resources").joinpath("records_examples.md").read_text(encoding="utf-8")

    return SYSTEM_PROMPT_TEMPLATE.format(
        query_format_doc=query_format_doc,
        examples_doc=examples_doc
    ).strip()

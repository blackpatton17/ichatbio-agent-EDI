import importlib
import json
import instructor
from openai import AsyncOpenAI
from tenacity import AsyncRetrying
from instructor.exceptions import InstructorRetryException

import requests
import os
import xml.etree.ElementTree as ET

from typing import Dict

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from schema import CodeGenerationRequestModel, MetadataExtractionResponseModel
from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts
from util.s3 import S3Client
from util.xml_to_dict import xml_to_dict
    

entrypoint = AgentEntrypoint(
    id="prompt_generation",
    description="Up to user's request and feeded context, for example, metadata of a dataset, generate code to analyze the dataset.",
    parameters=CodeGenerationRequestModel,
)

async def run(self, context: ResponseContext, request: str, params: CodeGenerationRequestModel):
    async with context.begin_process(summary="Fetch metadata") as process:
        try: 
            metadata_schema = await _fetch_package_metadata_schema(params.id)
            await process.log(f"Fetched metadata schema for {params.id}")
            
        except AIGenerationException as e:
            await process.log(f"Error fetching metadata schema: {e}")
            await context.reply(f"Error fetching metadata schema: {e}")
            return
        try:
            essential_keys = await _extract_essential_metadata(metadata_schema)
            await process.log(f"Extracted essential keys: {essential_keys}")
        except AIGenerationException as e:
            await process.log(f"Error extracting essential keys: {e}")
            await context.reply(f"Error extracting essential keys: {e}")
            return
        await context.reply(f"Essential keys extracted")
        
        # context.reply(f"Received request: {params.id}, feature working in progress...")

async def _fetch_package_metadata_schema(id: str) -> Dict:
    s3_key = f"{id.replace('.', '_')}/metadata_schema.json"
    client = S3Client()
    if client.object_exists(s3_key):
        url = client.get_s3_url(s3_key)
    else:
        raise AIGenerationException(f"Metadata schema for {id} not found in S3.")
    async for attempt in AsyncRetrying(
        stop=StopOnTerminalErrorOrMaxAttempts(max_attempts=3),
        reraise=True,
    ):
        with attempt:
            response = requests.get(url)
            if response.status_code != 200:
                raise AIGenerationException(f"Failed to fetch metadata schema from {url}")
            return json.loads(response.text)
        
async def _extract_essential_metadata(metadata: Dict) -> Dict:
    api_key = os.getenv("OPENAI_API_KEY")
    client: AsyncOpenAI = instructor.from_openai(
        AsyncOpenAI(api_key=api_key)
    )
    system_prompt = get_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract essential keys from the following metadata:\n{metadata}"}
    ]

    try:
        result = await client.chat.completions.create(
            model="gpt-4.1",
            temperature=0,
            response_model=MetadataExtractionResponseModel,
            messages=messages
        )
    except InstructorRetryException as e:
        raise AIGenerationException(e)

    return result.essential_keys

SYSTEM_PROMPT_TEMPLATE = """
You are extracting essential keys from the schema metadata.

# Query format

Here is a description of how EDI queries are formatted:

[BEGIN extraction instruction]

{instruction_doc}

[END extraction instruction]

"""

def get_system_prompt():
    extraction_instruction = importlib.resources.files("resources").joinpath("extraction_of_key_index_in_metadata_schema.md").read_text(encoding="utf-8")

    return SYSTEM_PROMPT_TEMPLATE.format(
        instruction_doc=extraction_instruction
    ).strip()
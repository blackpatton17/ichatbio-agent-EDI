from tenacity import AsyncRetrying

import requests
import os
import xml.etree.ElementTree as ET

from typing import Dict

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from schema import AnalysisRequestModel
from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts
from util.s3 import S3Client
from util.xml_to_dict import xml_to_dict
    

entrypoint = AgentEntrypoint(
    id="analyze_dataset",
    description="Query a detailed dataset's metadata from the EDI repository using a natural language request.",
    parameters=AnalysisRequestModel,
)

async def run(self, context: ResponseContext, request: str, params: AnalysisRequestModel):
    async with context.begin_process(summary="Fetch metadata") as process:
        await process.log(f"Received request: {params.id}")
        bucket_name = os.environ.get("S3_BUCKET_NAME") or "ichatbio-edi-agent-artifact-test"
        s3_client = S3Client(bucket_name=bucket_name)
        s3_key = f"{params.id.replace('.', '_')}/metadata.json"

        try:
            object_exists = s3_client.object_exists(s3_key)
            if object_exists:
                await process.log(f"Object already exists at s3://{bucket_name}/{s3_key}")
            else:
                try:
                    url = f"https://pasta.lternet.edu/package/metadata/eml/{params.id.replace('.', '/')}"
                    await process.log(f"Fetching metadata from {url}")
                    metadata = await _fetch_package_metadata(url)
                except Exception as e:
                    await process.log(f"Error fetching metadata: {e}")
                    await process.reply(f"Error fetching metadata: {e}")
                    return
                await process.log(f"Fetched metadata")
                s3_client.upload_json(s3_key, metadata)
                await process.log(f"Uploaded metadata to s3://{bucket_name}/{s3_key}")
            s3_url = s3_client.get_s3_url(s3_key)
            await process.create_artifact(
                mimetype="application/json",
                description=f"Metadata for dataset {params.id}",
                uris=[s3_url],
                metadata={"api_query_url": s3_url}
            )
            await context.reply("Metadata processed successfully.")
        except Exception as e:
            await process.reply(f"Error with S3 operations: {e}")
            return

async def _fetch_package_metadata(url: str) -> Dict:
    """
    Fetch the metadata of a package in EDI repository using the provided URL.
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
            return xml_to_dict(ET.fromstring(response.text))


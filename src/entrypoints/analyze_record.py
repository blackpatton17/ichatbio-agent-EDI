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

from typing import Dict

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint
# from ..schema import IDigBioRecordsApiParameters
# from ..util import ai

from schema import AnalysisRequestModel
from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts
import json
import re
import boto3
    

entrypoint = AgentEntrypoint(
    id="analyze_dataset",
    description="Query a detailed dataset's metadata from the EDI repository using a natural language request.",
    parameters=AnalysisRequestModel,
)

async def run(self, context: ResponseContext, request: str, params: AnalysisRequestModel):
    async with context.begin_process(summary="Fetch metadata") as process:
        await process.log(f"Received request: {params.id}")
        s3_endpoint = os.environ.get("PERSONAL_MINIO")
        aws_access_key_id = os.environ.get("MINIO_TEST_NAME")
        aws_secret_access_key = os.environ.get("MINIO_TEST_KEY")
        if not bucket_name:
            await process.log("S3_BUCKET_NAME environment variable not set.")
            return {"error": "S3 bucket name not configured."}

        s3_key = f"{params.id.replace('.', '_')}/metadata.json"
        
        # Configure S3 client with credentials and endpoint
        s3_client_config = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
        }
        if s3_endpoint:
            s3_client_config["endpoint_url"] = s3_endpoint
        
        s3_client = boto3.client("s3", **s3_client_config)

        try:
            # Check if the object already exists in S3
            try:
                s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                await process.log(f"Object already exists at s3://{bucket_name}/{s3_key}")
                object_exists = True
            except s3_client.exceptions.NoSuchKey:
                await process.log(f"Object does not exist, will upload to s3://{bucket_name}/{s3_key}")
                object_exists = False
            except Exception as e:
                await process.log(f"Error checking object existence: {e}")
                object_exists = False
            
            # Only upload if the object doesn't exist or if you want to overwrite
            if not object_exists:
                try:
                    url = f"https://pasta.lternet.edu/package/metadata/eml/{params.id.replace('.', '/')}"
                    await process.log(f"Fetching metadata from {url}")
                    metadata = await _fetch_package_metadata(url)
                except Exception as e:
                    await process.log(f"Error fetching metadata: {e}")
                    await process.reply(f"Error fetching metadata: {e}")
                    return
                
                await process.log(f"Fetched metadata")
                bucket_name = "ichatbio-edi-agent-artifact-test"
                metadata_json = json.dumps(metadata, indent=2)
                s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=metadata_json, ContentType="application/json")
                await process.log(f"Uploaded metadata to s3://{bucket_name}/{s3_key}")
            else:
                await process.log(f"Skipped upload - metadata already exists at s3://{bucket_name}/{s3_key}")
            
            s3_url = f"{s3_endpoint}/{bucket_name}/{s3_key}" if s3_endpoint else f"s3://{bucket_name}/{s3_key}"
            await process.create_artifact(
                mimetype="application/json",
                description=f"Here are the top 5 matching datasets from {s3_url}",
                uris=[s3_url],
                metadata={"api_query_url": s3_url}
            )
            await context.reply("Metadata processed successfully.")
        except Exception as e:
            await process.reply(f"Error with S3 operations: {e}")
            return


def _xml_to_dict(eml: ET.Element) -> Dict:
    """
    Convert an EML XML string to a dictionary.
    This function parses the XML and converts it to a nested dictionary structure.
    :param eml: The EML XML string to convert.
    :return: A dictionary representation of the EML XML.
    """

    element = eml
    node = {}
    if element.attrib:
        node.update(element.attrib)
    if element.text and element.text.strip():
        node['text'] = element.text.strip()
    # Add children
    for child in element:
        child_dict = _xml_to_dict(child)
        tag = child.tag.split('}', 1)[-1]  # Remove namespace if present
        if tag in node:
            # If tag already exists, convert to list
            if not isinstance(node[tag], list):
                node[tag] = [node[tag]]
            node[tag].append(child_dict)
        else:
            node[tag] = child_dict
    return node

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
            return _xml_to_dict(ET.fromstring(response.text))


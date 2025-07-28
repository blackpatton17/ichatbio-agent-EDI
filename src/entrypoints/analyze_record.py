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
    

entrypoint = AgentEntrypoint(
    id="analyze_record",
    description="Query a detailed record's metadata from the EDI repository using a natural language request.",
    parameters=AnalysisRequestModel,
)

async def run(self, context: ResponseContext, request: str, params: AnalysisRequestModel) -> Dict[str, str]:
    async with context.begin_process(summary="Fetch metadata") as process:
        process.log(f"Received request: {request}")
        # TODO: find somewhere to cache the metadata instead of fetching it every time
        try:
            metadata = await _fetch_package_metadata(params.url)
        except Exception as e:
            process.log(f"Error fetching metadata: {e}")
        process.log(f"Fetched metadata")

def _xml_to_dict(eml_str: str) -> Dict:
    """
    Convert an EML XML string to a dictionary.
    This function parses the XML and converts it to a nested dictionary structure.
    :param eml_str: The EML XML string to convert.
    :return: A dictionary representation of the EML XML.
    """

    element = ET.fromstring(eml_str)
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

async def _fetch_package_metadata(url: str) -> requests.Response:
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
            return _xml_to_dict(response.text)


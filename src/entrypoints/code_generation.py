from tenacity import AsyncRetrying

import requests
import os
import xml.etree.ElementTree as ET

from typing import Dict

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from schema import CodeGenerationRequestModel
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
        process.reply(f"Received request: {params.id}, feature working in progress...")
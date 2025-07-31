import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from ichatbio.agent_response import DirectResponse, ProcessBeginResponse, ProcessLogResponse, ArtifactResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from agent import EDIAgent
from schema import AnalysisRequestModel
from entrypoints.fetch_dataset_metadata import run, _fetch_package_metadata

# @pytest.mark.asyncio
# async def test_edi_search_basic(context, messages):
#     agent = EDIAgent()

#     # Simulate agent query
#     response = await agent.run(
#         context,
#         "Help me to understand the metadata of dataset edi.1357.1",
#         "search_dataset",
#         AnalysisRequestModel(id="edi.1357.1")
#     )

#     print(f"Messages: {messages}")

@pytest.mark.asyncio
async def test_fetch_dataset_metadata_run_success(context, messages):
    params = AnalysisRequestModel(id="edi.1357.1")
            
    # Call the run function (note: removed self parameter)
    result = await run(None, context, "Test request", params)
    print(f"Messages: {messages}")
    # result = await _fetch_package_metadata("https://pasta.lternet.edu/package/metadata/eml/edi/1357/1")

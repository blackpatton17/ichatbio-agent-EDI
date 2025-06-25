import asyncio
import pytest
from agent import _generate_records_search_parameters, SimplePASTAQuery



@pytest.mark.asyncio
async def test_generate_search_parameters_from_prompt():
    request = "Show me the sampling protocols used in vegetation plots at the Blue River site of the Andrews Experimental Forest."
    search_params, artifact_description = await _generate_records_search_parameters(request)

    assert isinstance(search_params, SimplePASTAQuery), "search_parameters should be a SimplePASTAQuery instance"
    assert hasattr(search_params, "q"), "'q' field must exist in search_parameters"
    assert isinstance(artifact_description, str) and artifact_description.strip(), "artifact_description should be a non-empty string"

    print("Search Parameters:", search_params)
    print("Artifact Description:", artifact_description)

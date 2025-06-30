import asyncio
import pytest
from agent import _generate_records_search_parameters, SimplePASTAQuery



@pytest.mark.asyncio
async def test_generate_search_parameters_from_prompt():
    request = "Retrieve datasets with atmospheric CO₂ concentrations and air temperature readings in the Andrews Forest with scope of knb-lter-and. " \
        "I also need the abstract and methods in the result",
    search_params, artifact_description = await _generate_records_search_parameters(request)

    assert isinstance(search_params, SimplePASTAQuery), "search_parameters should be a SimplePASTAQuery instance"
    assert hasattr(search_params, "q"), "'q' field must exist in search_parameters"
    assert isinstance(artifact_description, str) and artifact_description.strip(), "artifact_description should be a non-empty string"

    print("Search Parameters:", search_params)
    print("Artifact Description:", artifact_description)

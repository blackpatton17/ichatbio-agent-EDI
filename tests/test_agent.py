import sys
import os
import pytest

from ichatbio.agent_response import DirectResponse, ProcessBeginResponse, ProcessLogResponse, ArtifactResponse

# Add src/ to Python path to import EDIAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agent import EDIAgent


@pytest.mark.asyncio
async def test_edi_search_basic(context, messages):
    agent = EDIAgent()

    # Simulate agent query
    response = agent.run(
        context,
        "Retrieve datasets with atmospheric carbon dioxide concentrations and air temperature readings in the Andrews Forest with scope of knb-lter-and. " \
        "I also need the abstract and methods in the result",
        "search_dataset",
        None
    )

    # Collect messages
    messages: list[DirectResponse | ProcessBeginResponse | ProcessLogResponse | ArtifactResponse]

    # # Extract components
    # summaries = [m.summary for m in messages if isinstance(m, ProcessMessage) and m.summary]
    # texts = [m.text for m in messages if isinstance(m, TextMessage) and m.text]
    # artifacts = [m for m in messages if isinstance(m, ArtifactMessage)]

    # # Assertions
    # assert any("Generating EDI query" in s for s in summaries)
    # assert any("Query constructed" in s for s in summaries)
    # assert len(artifacts) == 1

    # artifact = artifacts[0]
    # print(f"Artifact url: {artifact.description}")
    # assert artifact.mimetype == "application/json"
    # assert artifact.content is not None
    # assert b"datasets" in artifact.content  # optional: verify content includes expected structure
    # print(f"Artifact: {artifact.content}")

import pytest
import sys
import os

from ichatbio.types import ArtifactMessage, ProcessMessage, TextMessage

# Add src/ to Python path to import EDIAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agent import EDIAgent, SearchEMLParameters


@pytest.mark.asyncio
async def test_edi_search_basic():
    agent = EDIAgent()
    response = agent.run(
        "Find me disturbance datasets from EDI",
        "search_dataset",
        SearchEMLParameters(keywords="disturbance")
    )
    messages = [m async for m in response]

    # Extract process message summaries
    summaries = [m.summary for m in messages if isinstance(m, ProcessMessage) and m.summary]
    text = [m.text for m in messages if isinstance(m, TextMessage) and m.text]
    artifacts = [p for p in messages if type(p) is ArtifactMessage]

    assert "Generating EDI query" in summaries
    assert "Query constructed" in summaries
    # assert "URL constructed" in text
    assert len(artifacts) == 1

    artifact = artifacts[0]
    assert artifact.mimetype == "application/json"
    assert artifact.content
    # assert artifact.metadata == {"api_query_url": "https://cataas.com/cat/sphynx"}
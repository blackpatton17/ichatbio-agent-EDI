# ichatbio-agent-example

Reference code for making new iChatBio agents.

## Quickstart

*Requires python 3.10 or higher*

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Start up the agent web server
python3 src
```

If everything worked, you should be able to find your agent card at http://localhost:9999/.well-known/agent.json.


test agent
`PYTHONPATH=src pytest -s tests/test_agent.py`
test llm `PYTHONPATH=src pytest -s tests/test_prompt_parsing.py`
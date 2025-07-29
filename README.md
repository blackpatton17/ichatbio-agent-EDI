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

If everything worked, you should be able to find your agent card at http://localhost:8000/.well-known/agent.json.

Add OPENAI_API_KEY to env
```sh
export OPENAI_API_KEY=<your key>
```


test agent
```py
pytest -s tests/test_search.py
```


test llm 
```py
pytest -s tests/test_prompt_parsing.py
```

 Command to run docker container in `run.sh`
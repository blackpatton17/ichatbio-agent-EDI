import a2a.types
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from ichatbio.agent_executor import IChatBioAgentExecutor

from src.agent import CataasAgent

if __name__ == "__main__":
    agent = CataasAgent()

    request_handler = DefaultRequestHandler(
        agent_executor=IChatBioAgentExecutor(agent),
        task_store=InMemoryTaskStore(),
    )

    card = agent.get_agent_card()

    a2a_agent_card = a2a.types.AgentCard(
        name=card.name,
        description=card.description,
        url="http://localhost:9999/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=a2a.types.AgentCapabilities(),
        skills=[a2a.types.AgentSkill(
            id=e.id,
            name=e.id,
            description=e.description,
            tags=[]
        ) for e in card.entrypoints]
    )

    server = A2AStarletteApplication(
        agent_card=agent.get_agent_card(), http_handler=request_handler
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=9999)
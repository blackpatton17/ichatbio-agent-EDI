from typing import Optional
# , Literal, AsyncGenerator, Dict, List, Union
from typing_extensions import override
from pydantic import Field, BaseModel

import instructor
from instructor.exceptions import InstructorRetryException

from ichatbio.agent import IChatBioAgent
from ichatbio.types import AgentCard, AgentEntrypoint
from ichatbio.agent_response import ResponseContext

from entrypoints import record_query

from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts


# EDIResponseFormat = Literal["png", "json"]


class EDIAgent(IChatBioAgent):
    def __init__(self):
        self.agent_card = AgentCard(
            name="EDI Dataset Agent",
            description="Searches datasets from PASTA+ EDI repository.",
            icon=None,
            entrypoints=[
                record_query.entrypoint
            ]
        )

    @override
    def get_agent_card(self) -> AgentCard:
        return self.agent_card

    @override
    async def run(self, context: ResponseContext, request: str, entrypoint: str, params: Optional[BaseModel]):
        match params:
            case None:
                await record_query.run(self, context, request)
            case _:
                await record_query.run(self, context, request)


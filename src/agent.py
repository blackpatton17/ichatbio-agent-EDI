from typing import Optional
# , Literal, AsyncGenerator, Dict, List, Union
from typing_extensions import override
from pydantic import Field, BaseModel

import instructor
from instructor.exceptions import InstructorRetryException

from ichatbio.agent import IChatBioAgent
from ichatbio.types import AgentCard, AgentEntrypoint
from ichatbio.agent_response import ResponseContext

from entrypoints import search_record, analyze_record

from util.ai import AIGenerationException, StopOnTerminalErrorOrMaxAttempts


# EDIResponseFormat = Literal["png", "json"]


class EDIAgent(IChatBioAgent):
    def __init__(self):
        self.agent_card = AgentCard(
            name="EDI Dataset Agent",
            description="Searches datasets from PASTA+ EDI repository.",
            icon=None,
            entrypoints=[
                search_record.entrypoint,
                analyze_record.entrypoint
            ]
        )

    @override
    def get_agent_card(self) -> AgentCard:
        return self.agent_card

    @override
    async def run(self, context: ResponseContext, request: str, entrypoint: str, params: Optional[BaseModel]):
        match entrypoint:
            case search_record.entrypoint.id:
                await search_record.run(self, context, request)
            case analyze_record.entrypoint.id:
                await analyze_record.run(self, context, request, params)
            case None:
                await context.error("No entrypoint specified.")
            case _:
                await search_record.run(self, context, request)


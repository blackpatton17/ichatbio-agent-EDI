import importlib.resources

import instructor
from instructor import AsyncInstructor
from instructor.exceptions import InstructorRetryException
from openai import AsyncOpenAI
from pydantic import Field, BaseModel
from tenacity import AsyncRetrying

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint
# from ..schema import IDigBioRecordsApiParameters
# from ..util import ai


entrypoint = AgentEntrypoint(
    id="search_dataset",
    description="Searches EDI for datasets using metadata or keyword search.",
    parameters=None,
)


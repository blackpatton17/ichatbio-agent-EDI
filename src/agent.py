import os
import urllib.parse
from typing import Optional, Literal, AsyncGenerator
from typing_extensions import override
from urllib.parse import urlencode

import dotenv
import instructor
import pydantic
import requests
from instructor.exceptions import InstructorRetryException
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic import Field

from ichatbio.agent import IChatBioAgent
from ichatbio.types import AgentCard, AgentEntrypoint, ProcessMessage
from ichatbio.types import Message, TextMessage, ArtifactMessage
import json

import xml.etree.ElementTree as ET

dotenv.load_dotenv()

EDIResponseFormat = Literal["png", "json"]


class SearchEMLParameters(BaseModel):
    scope: Optional[str] = None
    identifier: Optional[str] = None
    keywords: Optional[str] = None  # e.g., full-text search


class EDIAgent(IChatBioAgent):
    def __init__(self):
        self.agent_card = AgentCard(
            name="EDI Dataset Agent",
            description="Searches datasets from PASTA+ EDI repository.",
            entrypoints=[
                AgentEntrypoint(
                    id="search_dataset",
                    description="Searches EDI for datasets using metadata or keyword search.",
                    parameters=SearchEMLParameters
                )
            ]
        )

    @override
    def get_agent_card(self) -> AgentCard:
        return self.agent_card

    @override
    async def run(self, request: str, entrypoint: str, params: Optional[BaseModel]) -> AsyncGenerator[Message, None]:
        # openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        instructor_client = instructor.patch(openai_client)

        try:
            yield ProcessMessage(summary="Generating EDI query", description="Parsing user intent")

            edi_query: EDIQueryModel = await instructor_client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_model=EDIQueryModel,
                messages=[
                    {"role": "system",
                    "content": "You translate user requests into query parameters for the PASTA+ EDI Data Package Manager API."},
                    {"role": "user", "content": request}
                ],
                max_retries=3
            )

            url = edi_query.to_url()

            yield ProcessMessage(
                summary="Query constructed",
                description=f"Using structured parameters to query EDI, url: {url}",
                data={"search_parameters": edi_query.model_dump(exclude_none=True)}
            )

            yield ProcessMessage(description=f"Sending GET request to {url}")

            response = requests.get(url)

            if response.status_code != 200:
                yield TextMessage(text=f"Query failed with status code {response.status_code}")
                return
            
            yield ProcessMessage(
                summary="Datasets retrieved"
            )

            results = response.text.strip()

            if not results:
                yield TextMessage(text="No datasets matched your query.")
            else:
                entries = []
                root = ET.fromstring(results)
                # only take 10 top results
                for doc in root.findall("document")[:10]:
                    packageid = doc.findtext("packageid")
                    keywords = [kw.text for kw in doc.findall("keywords/keyword")]
                    # keywords_str = ", ".join(keywords)
                    title = doc.findtext("title")
                    # combined = f"{title} \n {keywords_str}".strip()
                    # entries.append(f"- {packageid}: {combined} \n")
                    entries.append({
                        "packageid": packageid,
                        "title": title,
                        "keywords": keywords
                    })

                # yield TextMessage(text="Top 10 matching dataset found:\n" + "\n".join(entries))
                # yield TextMessage(text="Top 10 matching dataset")
                yield ArtifactMessage(
                    mimetype="application/json",
                    description="Here are the top 10 matching datasets:",
                    content=json.dumps({"datasets": entries}).encode("utf-8")
                )


        except InstructorRetryException as e:
            yield TextMessage(text="Sorry, I couldn't find any dataset.")


class EDIQueryModel(BaseModel):
    scope: Optional[str] = Field(None, description="The data scope (e.g., 'edi', 'knb', etc.)")
    # identifier: Optional[str] = Field(None, description="Dataset identifier number")
    keywords: Optional[str] = Field(None, description="Keyword-based full-text search")

    def to_url(self):
        # base_url = "https://pasta.lternet.edu/package/search/eml?defType=edismax\
        #             &q=title:sediment+OR+keyword:disturbance&fl=packageid,keyword\
        #             &sort=score,desc&sort=packageid,asc&debug=false&start=0&rows=1000"
        url = "https://pasta.lternet.edu/package/search/eml"

        query_params = {
            "defType": "edismax",
            "fq": "scope:edi",
            "fl": "packageid,keyword,title",
            "sort": "score,desc",
            "start": 0,
            "rows": 1000,
            "debug": "false"
        }
        if self.scope:
            query_params["fq"] = f"scope:{self.scope}"
        if self.keywords:
            query_params["q"] = f"keyword:{self.keywords}"

        if query_params:
            url += "?" + urlencode(query_params)

        return url

COLORS = Literal[
    "white", "lightgray", "gray", "black", "red", "orange", "yellow", "green", "blue", "indigo", "violet", "pink"]


class MessageModel(BaseModel):
    """Parameters for adding messages to images."""

    text: str = Field(description="Text to add to the picture.")
    font_size: Optional[int] = Field(None,
                                     description="Font size to use for the added text. Default is 50. 10 is barely readable. 200 might not fit on the picture.")
    font_color: Optional[COLORS] = Field(None, description="Font color to use for the added text. Default is white.",
                                         examples=["red", "green", "yellow", "pink", "gray"])

    @pydantic.field_validator("font_size")
    @classmethod
    def validate_font_size(cls, v):
        if v <= 0:
            raise ValueError("font_size must be positive")
        return v


# class CatModel(BaseModel):
#     """API parameters for https://cataas.com."""

#     tags: Optional[list[str]] = Field(None,
#                                       description="One-word tags that describe the cat image to return. Leave blank to get any kind of cat picture.",
#                                       examples=[["orange"], ["calico", "sleeping"]])
#     message: Optional[MessageModel] = Field(None, description="Text to add to the picture.")

#     def to_url(self, format: CataasResponseFormat):
#         url = "https://cataas.com/cat"
#         params = {}

#         if format == "json":
#             params |= {"json": True}

#         if self.tags:
#             url += "/" + ",".join(self.tags)

#         if self.message:
#             url += f"/says/" + urllib.parse.quote(self.message.text)
#             if self.message.font_size:
#                 params |= {"fontSize": self.message.font_size}
#             if self.message.font_color:
#                 params |= {"fontColor": self.message.font_color}

#         if params:
#             url += "?" + urlencode(params)

#         return url

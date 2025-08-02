from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field
from pydantic import RootModel
from typing import Dict, Literal

# ------------ Coordinate and Date Range Models ---------------
class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class DateRangeValue(BaseModel):
    gte: Optional[datetime] = Field(None, description="Start date (inclusive)")
    lte: Optional[datetime] = Field(None, description="End date (inclusive)")


class BoundingBoxValue(BaseModel):
    left_top: Coordinate
    right_bottom: Coordinate


# --------------- Filter Field and Query Models ---------------
class FilterField(BaseModel):
    type: Literal["exact", "fulltext", "range", "prefix"]
    value: Union[str, dict]

class PASTAQuery(BaseModel):
    q: Optional[Dict[str, Dict[str, Literal["existed", "missing", "prefix"]]]] = Field(default_factory=dict)
    fq: Optional[Dict[str, FilterField]] = Field(default_factory=dict)
    fl: Optional[List[str]] = Field(default_factory=list)
    rows: Optional[int] = Field(default=1000)
    start: Optional[int] = Field(default=0)
    sort: Optional[str] = None

class EDIQueryModel(PASTAQuery):
    def to_url(self) -> str:
        base_url = "https://pasta.lternet.edu/package/search/eml"
        params = {}

        q_clauses = []
        intent_map = {
            "existed": "{field}{term}",
            "missing": "-{field}{term}",
            "prefix": "{field}{term}*",
        }

        for field_name, terms in self.q.items():
            for term, intent in terms.items():
                # Quote term if it contains spaces
                quoted_term = f"\"{term}\"" if " " in term else term
                # Compute the field part of the clause
                field = f"{field_name}:" if field_name != "uncategorized" else ""
                # Append using the appropriate pattern
                q_clauses.append(intent_map[intent].format(field=field, term=quoted_term))

        params["q"] = "+".join(q_clauses) if q_clauses else "*"

        fq_list = []
        for field, filter_obj in self.fq.items():
            if filter_obj.type == "range":
                val = filter_obj.value
                if hasattr(val, "gte") and hasattr(val, "lte"):
                    fq_list.append(f"{field}:[{val.gte} TO {val.lte}]")
                elif isinstance(val, dict):
                    top = val['left_top']
                    bottom = val['right_bottom']
                    fq_list.append(f"{field}:[{top['lat']},{top['lon']} TO {bottom['lat']},{bottom['lon']}]")
            else:
                fq_list.append(f"{field}:{filter_obj.value}")
        if fq_list:
            params["fq"] = fq_list

        if self.fl:
            params["fl"] = ",".join(self.fl)
        if self.rows:
            params["rows"] = str(self.rows)
        if self.start:
            params["start"] = str(self.start)
        if self.sort:
            params["sort"] = self.sort

        query_parts = []
        for param_key, param_value in params.items():
            if isinstance(param_value, list):
                for item in param_value:
                    query_parts.append(f"{param_key}={item}")
            else:
                query_parts.append(f"{param_key}={param_value}")
        return f"{base_url}?" + "&".join(query_parts)

class LLMQueryParamResponseModel(BaseModel):
    plan: str = Field(description="A brief explanation of what API parameters you plan to use")
    search_parameters: PASTAQuery = Field()
    artifact_description: str = Field(description="A concise characterization of the retrieved occurrence record data")

class LLMSummarizationResponseModel(BaseModel):
    summary: str = Field(description="A summary of the retrieved occurrence record data")


# --------------- Analysis Request Model ---------------
class AnalysisRequestModel(BaseModel):
    id: str = Field(
        description="The unique identifier of the record to fetch from the EDI repository.",
        example="edi.456.5"
    )

# --------------- Code Generation Request Model ---------------
class CodeGenerationRequestModel(BaseModel):
    id: str = Field(
        description="The unique identifier of the record to generate code for.",
        example="edi.456.5"
    )

class MetadataExtractionResponseModel(BaseModel):
    essential_keys: List[str] = Field(
        description="A list of essential keys extracted from the metadata."
    )
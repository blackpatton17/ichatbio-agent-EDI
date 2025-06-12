from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field
from pydantic import RootModel
from typing import Dict, Literal

class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class DateRangeValue(BaseModel):
    gte: Optional[datetime] = Field(None, description="Start date (inclusive)")
    lte: Optional[datetime] = Field(None, description="End date (inclusive)")


class BoundingBoxValue(BaseModel):
    left_top: Coordinate
    right_bottom: Coordinate


class FilterField(BaseModel):
    type: Literal["exact", "fulltext", "range", "prefix"]
    value: Union[str, DateRangeValue, BoundingBoxValue]


class SearchFieldIntent(RootModel[Dict[str, Literal["existed", "missing", "prefix"]]]):
    pass


class PASTAQuery(BaseModel):
    q: Optional[Dict[str, SearchFieldIntent]] = Field(default_factory=dict)
    fq: Optional[Dict[str, FilterField]] = Field(default_factory=dict)
    fl: Optional[List[str]] = Field(default_factory=list)
    rows: Optional[int] = Field(default=10, ge=1)
    start: Optional[int] = Field(default=0, ge=0)
    sort: Optional[str] = None

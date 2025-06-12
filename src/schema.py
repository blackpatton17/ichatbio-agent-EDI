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

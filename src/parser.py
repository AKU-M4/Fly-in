from path import Path
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Any, Tuple, Dict, List

class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(Basemodel):
    name: str
    x: int
    y: int
    zone_type: ZoneType = Zonetype.NORMAL
    color: Optional[str] = None
    max_drones : int = Field(default=1, ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if "-" in v or " " in v:
            raise ValueError(f"Zone name {v} cannot contain dashes or spaces.")
        return v
    
    @property
    def travel_cost(self) -> int:
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1
    
    
class Connection(BaseModel):
    zone_name: str
    zone_name2: str
    max_link_capacity: int = Field(default= 1, ge=1)
    
class Graph(BaseModel):
    
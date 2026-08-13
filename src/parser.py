from path import Path
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional, Any, Tuple, Dict, List

class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
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
    nb_drones : int = Field(default=0, ge=0)
    start_hub: Optional[Zone] = None
    end_hub: Optional[Zone] = None
    zones = Dict[str, Zone] = None
    connection : List[Connection] = Field(default_factory=list)
    adj_list: Dict[str, List[Connection]] = Field(default_factory=dict)

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name '{zone.name}' ")
        self.zones[zone.name] = zone
        self.adj_list[zone.name] = []

    def add_connectoion(self, conn: Connection) -> None:
        if conn.zone1_name not in self.zones or conn.zone2_name not in self.zones:
            raise ValueError(
                f"Connection links undefined zone: {conn.zone1_name}"
                f"or {conn.zone_2name}."
            )
        self.connections.append(conn)
        self.adj_list[conn.zone1_name].append(conn)
        self.adj_list[conn.zone2_name].append(conn)

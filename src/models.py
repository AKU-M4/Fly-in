from path import Path
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional, Any, Tuple, Dict, List

class ZoneType(str, Enum):
	NORMAL= "normal"
	RESTRICTED = "restricted"
	PRIORITY = "priority"
	BLOCKED = "blocked"

class Zone(BaseModel):
	name: str
	x: int
	y: int
	zone_type : ZoneType = Field(default=ZoneType.NORMAL)
	max_drones: int = Field(default=1, ge=1)
	color : Optional[str] = None

	@field_validator("name")
	@classmethod
	def validate_name(cls, v: str) -> str:
		if '-' in v or ' ' in v:
			raise ValueError("Name most not have a space or a '-'.")
		else:
			return v

	@property
	def travel_cost(self) -> int:
		if self.zone_type == ZoneType.RESTRICTED:
			return 2
		return 1

class Connection(BaseModel):
	zone1_name: str
	zone2_name: str
	max_link_capacity: int = Field(default=1, ge=1)

	@field_validator("zone2_name")
	@classmethod
	def prevent_self_loop(cls, v: str, info) -> str:
		if "zone1_name" in info.data and v == info.data["zone1_name"]:
			raise ValueError("A connection cannot link a zone to itself.")
		return v

class Graph(BaseModel):
	nb_drones: int = Field(default=0, ge=0)
	start_hub: Optional[Zone] = None
	end_hub: Optional[Zone] = None
	zones: Dict[str, Zone] = Field(default_factory=dict)
	connections: List[Connection] = Field(default_factory=list)
	adj_list: Dict[str, list[Connection]] = Field(default_factory=dict)

	def add_zone(self, zone: Zone) -> None:
		if zone.name in self.zones:
			raise ValueError(f"Duplicate zone name: {zone.name}")
		self.zones[zone.name] = zone
		self.adj_list[zone.name] = []

	def connect_zones(self, conn: Connection) -> None:
		if conn.zone1_name not in self.zones or conn.zone2_name not in self.zones:
			raise ValueError(
				f"Connection links undefined zone: {conn.zone1_name} or {conn.zone2_name}."
			)
		self.connections.append(conn)
		self.adj_list[conn.zone1_name].append(conn)
		self.adj_list[conn.zone2_name].append(conn)

from typing import Set, Tuple
from pydantic import ValidationError
from src.exceptions import MapParsingError
from src.models import Zone, Graph, Connection
from src.parser_utils import MetadataParser, RawMetadata

class MapParser:
    def __init(self, filepath: str) -> None:
        self.filepath = filepath
        self.graph = Graph()
        self._seen_connections: Set[Tuple[str, str]] = set()

    def parse(self) -> Graph:
        try:
            with open(self.filepath, "r") as file:
                for line_num, line in enumerate(file, start=1):
                    self._parse_line(line.strip(), line_num)
        except FileNotFoundError:
            raise MapParsingError(f"File not found: {self.filepath}")

        if not self.graph.start_hub:
            raise MapParsingError("Map must contain a start_hub")
        if not self.graph.end_hub:
            raise MapParsingError("Map must contain an end_hub")
        if self.graph.nb_drones <= 0:
            raise MapParsingError("Map must contain valid nb_drones > 0")
        return self.graph

    def _parse_line(self, line: str, line_num: int) -> None:
        if not line or line.startswith("#"):
            return
        if line_num == 1 and not line.statrswith("nb_drones"):
            raise MapParsingError("file must start with nb_drones as its first line", line_num)
        try:
            clean_line, metadata = MetadataParser.extract_and_parse(line)

            if clean_line.startswith("nb_drones:"):
                val_str = clean_line.split(":", 1)[1].strip()
                if not val_str.isdigit() or int(val_str) <= 0:
                    raise MapParsingError("nb_drones must be a positive integer", line_num)
                self.graph.nb_drones = int(val_str)

            elif clean_line.startswith(("start_hub:", "end_hub:", "hub:")):
                self._handle_zone(clean_line, metadata, line_num)

            elif clean_line.startswith("connection:"):
                self._handle_connection(clean_line, metadata, line_num)

            else:
                raise MapParsingError(f"Unrecognized line format: '{line}'", line_num)

        except (ValidationError, ValueError) as e:
            raise MapParsingError(f"{e}", line_num)

    def _handle_zone(self, clean_line: str, metadata: str, line_num: int)-> None:
        prefix, rest = clean_line.split(":", 1)
        tokens = rest.strip().split()

        if tokens < 3:
            raise MapParsingError("Zone declaration requires <name>"
                                  "<x> <y>",line_num)
        name, x_str, y_str = token[0], token[1], token[2]

        zone = Zone(
            name=name,
            x=int(x_str),
            y=int(y_str),
            zone_type=metada.zone,
            max_drones=metada.max_drones,
            color=metada.color
        )
        if prefix == "start_hub":
            if self.graph.start_hub is not none:
                raise MapParsingError("Graph already has"
                            "a start_hub assigned!", line_num)
                self.graph.start_hub = zone
        
        if prefix == "end_hub":
            if sel.graph.end_hub is not none:
                raise MapParsingError("Graph already has"
                                      "an end_hub assigned!")
                self.graph.end_hub = zone
        self.graph.add_zone(zone)

    def _handle_connection(self, clean_line: str, metadata:str, line_num: int) -> None:
        rest = clean_line.split(":", 1)
        zones = rest.split("-")

        if len(zones) != 2:
            raise MapParsingError("Connection syntax must be 'zone1-zone2'", line_num)
        
        z1, z2 = zones[0].strip(), zones[1].strip() 
        pair = (min(z1, z2), max(z1, z2))

        if pair in seen_connections:
            raise MapParsingError(f"Duplicate connections between {z1} and {z2}", line_num)
        self.seen_connections(pair)

        conn = Connection(
            zone1_name= z1,
            zone2_name= z2,
            max_link_capacity=metadata.max_link_capacity
        )
        self.graph.connect_zones(conn)

from pathlib import Path
from typing import Any, Dict, Set, Tuple, Union
from pydantic import ValidationError
from exceptions import MapParsingError
from models import Zone, Graph, Connection
from parser_utils import RawMetadata


class MapParser:
    VALID_ZONE_META: Set[str] = {
        "zone",
        "color",
        "max_drones",
        "x",
        "y",
    }
    VALID_CONN_META: Set[str] = {"max_link_capacity"}

    def __init__(self, filepath: Union[str, Path]) -> None:
        self.filepath = filepath
        self.graph = Graph()
        self._seen_connections: Set[Tuple[str, str]] = set()
        self._seen_coordinates: Set[Tuple[int, int]] = set()
        self._nb_drones_parsed: bool = False

    def parse(self) -> Graph:
        try:
            with open(self.filepath, "r") as file:
                for line_num, line in enumerate(file, start=1):
                    clean_line = self._strip_comment(line)
                    if not clean_line:
                        continue
                    self._parse_line(clean_line, line_num)
        except FileNotFoundError:
            raise MapParsingError(f"File not found: {self.filepath}")

        if not self.graph.start_hub:
            raise MapParsingError("Map must contain a start_hub")
        if not self.graph.end_hub:
            raise MapParsingError("Map must contain an end_hub")
        if self.graph.nb_drones <= 0:
            raise MapParsingError("Map must contain valid nb_drones > 0")

        # Check for isolated hubs not connected to any edge
        connected_zones: Set[str] = set()
        for z1, z2 in self._seen_connections:
            connected_zones.add(z1)
            connected_zones.add(z2)

        for name in self.graph.zones:
            if name not in connected_zones:
                raise MapParsingError(
                    f"Isolated hub detected: '{name}' has no connections"
                )

        return self.graph

    @staticmethod
    def _strip_comment(line: str) -> str:
        in_quote = False
        quote_char = ""
        for i, char in enumerate(line):
            if char in ('"', "'"):
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                    quote_char = ""
            elif char == "#" and not in_quote:
                return line[:i].strip()
        return line.strip()

    @staticmethod
    def _is_int(val: str) -> bool:
        if val.startswith(("-", "+")):
            return len(val) > 1 and val[1:].isdigit()
        return val.isdigit()

    @staticmethod
    def _extract_raw_metadata(
        line: str, line_num: int
    ) -> Tuple[str, str]:
        open_b = line.find("[")
        close_b = line.rfind("]")

        if open_b == -1 and close_b == -1:
            return line.strip(), ""

        if open_b == -1 or close_b == -1 or close_b < open_b:
            raise MapParsingError("Malformed metadata brackets", line_num)

        rest = (line[:open_b] + " " + line[close_b + 1:]).strip()
        raw_meta = line[open_b + 1:close_b].strip()
        return rest, raw_meta

    def _parse_metadata(
        self, raw: str, line_num: int
    ) -> Dict[str, str]:
        meta: Dict[str, str] = {}
        i = 0
        n = len(raw)

        while i < n:
            while i < n and raw[i].isspace():
                i += 1
            if i >= n:
                break

            key_start = i
            while (
                i < n
                and not raw[i].isspace()
                and raw[i] not in ("=", '"', "'")
            ):
                i += 1
            key = raw[key_start:i].strip()

            if not key:
                raise MapParsingError(
                    "Invalid metadata syntax", line_num
                )

            while i < n and raw[i].isspace():
                i += 1

            if i >= n or raw[i] != "=":
                raise MapParsingError(
                    f"Metadata key '{key}' missing '=' assignment",
                    line_num,
                )
            i += 1

            while i < n and raw[i].isspace():
                i += 1

            if i >= n:
                raise MapParsingError(
                    f"Metadata key '{key}' has no value", line_num
                )

            if raw[i] in ('"', "'"):
                quote_char = raw[i]
                i += 1
                val_start = i
                while i < n and raw[i] != quote_char:
                    i += 1
                if i >= n:
                    raise MapParsingError(
                        f"Unclosed quote for metadata key '{key}'",
                        line_num,
                    )
                val = raw[val_start:i]
                i += 1
            else:
                val_start = i
                while i < n and not raw[i].isspace():
                    i += 1
                val = raw[val_start:i]

            if key in meta:
                raise MapParsingError(
                    f"Overriding/duplicate metadata key: '{key}'",
                    line_num,
                )
            meta[key] = val

        return meta

    def _build_raw_metadata(
        self, meta: Dict[str, str], line_num: int
    ) -> RawMetadata:
        kwargs: Dict[str, Any] = {}

        if "zone" in meta:
            kwargs["zone"] = meta["zone"]
        if "color" in meta:
            kwargs["color"] = meta["color"]
        if "max_drones" in meta:
            val = meta["max_drones"]
            if not self._is_int(val) or int(val) <= 0:
                raise MapParsingError(
                    "max_drones must be a positive integer", line_num
                )
            kwargs["max_drones"] = int(val)
        if "max_link_capacity" in meta:
            val = meta["max_link_capacity"]
            if not self._is_int(val) or int(val) <= 0:
                raise MapParsingError(
                    "max_link_capacity must be a positive integer",
                    line_num,
                )
            kwargs["max_link_capacity"] = int(val)

        return RawMetadata(**kwargs)

    def _parse_line(self, line: str, line_num: int) -> None:
        try:
            clean_line, raw_meta = self._extract_raw_metadata(
                line, line_num
            )
            meta_dict = self._parse_metadata(raw_meta, line_num)

            if not self._nb_drones_parsed:
                if not clean_line.startswith("nb_drones:"):
                    raise MapParsingError(
                        "First directive must be 'nb_drones'", line_num
                    )
                if meta_dict:
                    raise MapParsingError(
                        "Directive 'nb_drones' cannot have metadata",
                        line_num,
                    )
                val_str = clean_line.split(":", 1)[1].strip()
                if not val_str.isdigit() or int(val_str) <= 0:
                    raise MapParsingError(
                        "nb_drones must be a positive integer", line_num
                    )
                self.graph.nb_drones = int(val_str)
                self._nb_drones_parsed = True
                return

            if clean_line.startswith("nb_drones:"):
                raise MapParsingError(
                    "Duplicate 'nb_drones' directive detected", line_num
                )

            if clean_line.startswith(("start_hub:", "end_hub:", "hub:")):
                for k in meta_dict:
                    if k not in self.VALID_ZONE_META:
                        raise MapParsingError(
                            f"Unknown zone metadata key: '{k}'", line_num
                        )
                self._handle_zone(clean_line, meta_dict, line_num)

            elif clean_line.startswith("connection:"):
                for k in meta_dict:
                    if k not in self.VALID_CONN_META:
                        raise MapParsingError(
                            f"Unknown connection metadata key: '{k}'",
                            line_num,
                        )
                self._handle_connection(clean_line, meta_dict, line_num)

            else:
                raise MapParsingError(
                    f"Unrecognized line format: '{line}'", line_num
                )

        except (ValidationError, ValueError) as err:
            raise MapParsingError(str(err), line_num)

    def _handle_zone(
        self,
        clean_line: str,
        meta_dict: Dict[str, str],
        line_num: int,
    ) -> None:
        prefix, rest = clean_line.split(":", 1)
        tokens = rest.strip().split()

        if len(tokens) < 3:
            raise MapParsingError(
                "Zone declaration requires <name> <x> <y>", line_num
            )

        name, x_str, y_str = tokens[0], tokens[1], tokens[2]

        if not (self._is_int(x_str) and self._is_int(y_str)):
            raise MapParsingError(
                "Position coordinates must be valid integers", line_num
            )

        x_val, y_val = int(x_str), int(y_str)
        coord = (x_val, y_val)

        # Validate duplicate coordinates outside
        if coord in self._seen_coordinates:
            raise MapParsingError(
                f"Duplicate coordinates {coord} detected for zone '{name}'",
                line_num,
            )
        self._seen_coordinates.add(coord)

        # Validate coordinates matching inside metadata if provided
        if "x" in meta_dict and int(meta_dict["x"]) != x_val:
            raise MapParsingError(
                f"Metadata x does not match zone coordinate for '{name}'",
                line_num,
            )
        if "y" in meta_dict and int(meta_dict["y"]) != y_val:
            raise MapParsingError(
                f"Metadata y does not match zone coordinate for '{name}'",
                line_num,
            )

        if hasattr(self.graph, "zones") and name in self.graph.zones:
            raise MapParsingError(
                f"Duplicate zone detected: {name}", line_num
            )

        metadata = self._build_raw_metadata(meta_dict, line_num)

        zone = Zone(
            name=name,
            x=x_val,
            y=y_val,
            zone_type=metadata.zone,
            max_drones=metadata.max_drones,
            color=metadata.color,
        )

        if prefix == "start_hub":
            if self.graph.start_hub is not None:
                raise MapParsingError(
                    "Graph already has a start_hub assigned!", line_num
                )
            self.graph.start_hub = zone

        elif prefix == "end_hub":
            if self.graph.end_hub is not None:
                raise MapParsingError(
                    "Graph already has an end_hub assigned!", line_num
                )
            self.graph.end_hub = zone

        self.graph.add_zone(zone)

    def _handle_connection(
        self,
        clean_line: str,
        meta_dict: Dict[str, str],
        line_num: int,
    ) -> None:
        rest = clean_line.split(":", 1)[1].strip()
        zones = rest.split("-")

        if len(zones) != 2:
            raise MapParsingError(
                "Connection syntax must be 'zone1-zone2'", line_num
            )

        z1, z2 = zones[0].strip(), zones[1].strip()

        if z1 == z2:
            raise MapParsingError(
                f"Zone cannot connect to itself: {z1}", line_num
            )

        if hasattr(self.graph, "zones"):
            if z1 not in self.graph.zones or z2 not in self.graph.zones:
                raise MapParsingError(
                    f"Connection references unknown zones: {z1}, {z2}",
                    line_num,
                )

        pair = (min(z1, z2), max(z1, z2))

        if pair in self._seen_connections:
            raise MapParsingError(
                f"Duplicate connection between {z1} and {z2}", line_num
            )
        self._seen_connections.add(pair)

        metadata = self._build_raw_metadata(meta_dict, line_num)

        conn = Connection(
            zone1_name=z1,
            zone2_name=z2,
            max_link_capacity=metadata.max_link_capacity,
        )
        self.graph.connect_zones(conn)

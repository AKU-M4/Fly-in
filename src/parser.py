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

	def parse_line(self, line: str, line_num: int) -> None:
		if not line or line.startswith("#"):
			return
		try:
			clean_line, metadata = MetadataParser.extract_and_parse(line)

			if clean_line.startswith("nb_drones:"):
				val_str = clean_line.split(":", 1)[1].strip()
				if not val_str.isdigit() or int(val_str) <= 0:
					raise MapParsingError("nb_drones must be a positive integer", line_num)
				self.graph.nb_drones = val_str

			elif clean_line.startswith(("start_hub:", "end_hub", "hub:")):
				self._handle_zone(clean_line, metadata, line_num)

			elif clean_line.startswith("connection"):			
				if 
		except:

def _handle_zone(clean_line: str, metadata: str, line_num: int):


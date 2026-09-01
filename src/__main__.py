from src.models import Zone, ZoneType, Connection, Graph
from src.parser_utils import RawMetadata, MetadataParser
from src.parser import MapParser
from path import Path

MAP_PATH = Path("flyin/map.txt")


def main():
	map = MapParser(MAP_PATH)
	




if __name__ == "__main__":
	main()
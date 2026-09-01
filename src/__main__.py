from src.models import Zone, ZoneType, Connection, Graph


def main():
	print("--- 1. TESTING ALL VALID DATA")
	zone1 = Zone(name="talibanhub", x=10, y=10, color="red")
	print(f"{zone1.name}, {zone1.zone_type}, {zone1.x}, {zone1.y}, {zone1.color}")


	print("---2. TESTING VALID DATA FOR GRAPH AND CONNECTIONS ---")
	graph = Graph(max_drones=3)

	z_start = Zone(name="start_hub", x=0, y=0, color="blue")
	z_end = Zone(name="end_zone", x=2, y=2, color="green")
	z_hub = Zone(name="hub1", x=1, y=1, color="purple", zone_type=ZoneType.RESTRICTED)

	graph.add_zone(z_start)
	graph.add_zone(z_end)
	graph.add_zone(z_hub)
	graph.start_hub = z_start
	graph.end_hub = z_end

	c1 = Connection(zone1_name=z_start.name, zone2_name=z_hub.name)
	c2 = Connection(zone1_name=z_hub.name, zone2_name=z_end.name)

	graph.connect_zones(c1)
	graph.connect_zones(c2)

	print(f"Zones in Graph: {list(graph.zones.keys())}")
	print(f"Adjusted_list: {list(graph.connections)}")


if __name__ == "__main__":
	main()
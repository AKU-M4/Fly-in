import sys
from pathlib import Path
from src.exceptions import MapParsingError
from src.parser import MapParser
from src.router import PathFinder, TimeSpaceScheduler
from src.visualizer import Visualizer


def main() -> None:
    # Filter out custom flags like --gui to extract the map filepath
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    use_gui = "--gui" in sys.argv

    if not args:
        print("Usage: python main.py <map_filepath> [--gui]")
        sys.exit(1)

    map_path = Path(args[0])

    try:
        # 1. Parse and validate the graph
        parser = MapParser(str(map_path))
        graph = parser.parse()

        # 2. Find candidate shortest paths using Dijkstra
        path_finder = PathFinder(graph)
        candidate_paths = path_finder.find_k_paths(k=5)

        if not candidate_paths:
            print("Error: No valid path found from start_hub to end_hub")
            sys.exit(1)

        # 3. Schedule all drones through space and time
        scheduler = TimeSpaceScheduler(graph, candidate_paths)
        turn_movements = scheduler.schedule_all_drones()

        # 4. Render results (Terminal output or Pygame GUI)
        viz = Visualizer(graph)
        if use_gui:
            viz.render_gui(turn_movements)
        else:
            viz.render_terminal(turn_movements)

    except MapParsingError as e:
        print(f"Parsing Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Execution Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
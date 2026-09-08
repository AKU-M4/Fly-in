import sys
from pathlib import Path
from typing import Dict, List, Tuple
from exceptions import MapParsingError
from parser import MapParser
from router import PathFinder, Scheduler

ANSI_COLORS: Dict[str, str] = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "gray": "\033[90m",
    "gold": "\033[38;5;214m",
    "darkred": "\033[38;5;88m",
    "lightblue": "\033[38;5;117m",
    "purple": "\033[38;5;129m",
    "orange": "\033[38;5;208m",
    "darkgreen": "\033[38;5;22m",
    "reset": "\033[0m",
}


def main() -> None:
    show_cap = "--capacity-info" in sys.argv
    if show_cap:
        sys.argv.remove("--capacity-info")

    if len(sys.argv) != 2:
        print("Usage: python3 -m src <map_file>", file=sys.stderr)
        sys.exit(1)

    map_path = Path(sys.argv[1])

    try:
        parser = MapParser(map_path)
        graph = parser.parse()

        finder = PathFinder(graph)
        all_paths = finder.get_k_paths(k=8)

        if not all_paths:
            print("Error: No valid paths found from start to goal.",
                  file=sys.stderr)
            sys.exit(1)

        scheduler = Scheduler(graph, all_paths)
        moves = scheduler.run()

    except MapParsingError as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}", file=sys.stderr)
        sys.exit(1)

    turns_dict: Dict[int, List[Tuple[int, str]]] = {}

    for turn, drone_id, target in moves:
        if target in graph.zones:
            color_name = getattr(
                graph.zones[target], "color", "white"
            ).lower()
            color_code = ANSI_COLORS.get(color_name, "")
            reset_code = ANSI_COLORS["reset"] if color_code else ""

            colored_target = f"{color_code}{target}{reset_code}"
            turns_dict.setdefault(turn, []).append(
                (drone_id, f"D{drone_id}-{colored_target}")
            )
        else:
            turns_dict.setdefault(turn, []).append(
                (drone_id, f"D{drone_id}-{target}")
            )

    if turns_dict:
        max_turn = max(turns_dict.keys())
        for t in range(1, max_turn + 1):
            if t in turns_dict:
                sorted_tuples = sorted(turns_dict[t])
                turn_moves = [
                    move_str for _, move_str in sorted_tuples
                ]
                print(f" ".join(turn_moves))
                if show_cap:
                    for name, zone in graph.zones.items():
                        used = scheduler.table.node_traffic.get((name, t), 0)
                        if used > 0:
                            print(
                                f"  Zone {name}: {used}/{zone.max_drones} "
                                "drones"
                            )

                    for (edge, turn), used in (
                        scheduler.table.edge_traffic.items()
                    ):
                        if turn == t and used > 0:
                            u, v = edge
                            print(
                                f"  Connection {u}-{v}: {used} capacity used"
                            )


if __name__ == "__main__":
    main()

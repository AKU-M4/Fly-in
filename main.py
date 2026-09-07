import sys
from parser import MapParser
from router import PathFinder, Scheduler
from pathlib import Path

ANSI_COLORS = {
    # The basic colors (16-color standard)
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "gray": "\033[90m",

    # Extended 256-color palette (\033[38;5;Number m)
    "gold": "\033[38;5;214m",
    "darkred": "\033[38;5;88m",
    "lightblue": "\033[38;5;117m",
    "purple": "\033[38;5;129m",
    "orange": "\033[38;5;208m",
    "darkgreen": "\033[38;5;22m",

    # The Off Switch
    "reset": "\033[0m"
}


def main() -> None:
    if len(sys.argv) != 2:
        print("Please provide a map file path.")
        sys.exit(1)

    map_path = Path(sys.argv[1])

    parser = MapParser(map_path)
    graph = parser.parse()

    finder = PathFinder(graph)
    all_paths = finder.get_k_paths(k=8)

    if not all_paths:
        print("No paths were found!")
        sys.exit(1)

    scheduler = Scheduler(graph, all_paths)
    moves = scheduler.run()

    turns_dict = {}
    for turn, drone_id, target in moves:
        print(turn, drone_id, target)
        if target in graph.zones:
            color_name = getattr(graph.zones[target], "color").lower()
            color_code = ANSI_COLORS.get(color_name, "")
            reset_code = ANSI_COLORS["reset"] if color_code else ""

            colored_target = f"{color_code}{target}{reset_code}"
            turns_dict.setdefault(turn, []).append(
                (drone_id, f"D{drone_id}-" f"{colored_target}")
            )
        else:
            turns_dict.setdefault(turn, []).append(
                (drone_id, f"D{drone_id}-{target}")
            )

    print(turns_dict)
    if turns_dict:
        max_turn = max(turns_dict.keys())

        for t in range(1, max_turn + 1):
            if t in turns_dict:
                sorted_tuples = sorted(turns_dict[t])
                turn_moves = [
                    move_string for drone_id, move_string in sorted_tuples]

                print(f"Turn {t:02d}:" + "".join(turn_moves))


if __name__ == "__main__":
    main()

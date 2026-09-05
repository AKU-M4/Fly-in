import sys
from src.parser import MapParser
from src.router import PathFinder, Scheduler

def main():
    if len(sys.argv) < 2:
        print("Please provide a map file path.")
        sys.exit(1)

    map_path = sys.argv[1]
    
    # 1. Parse Graph
    parser = MapParser(map_path)
    graph = parser.parse()

    # 2. Find MULTIPLE optimized paths (K=8 handles complex maps well)
    finder = PathFinder(graph)
    paths = finder.get_k_paths(k=8)

    if not paths:
        print("Error: No paths found!")
        sys.exit(1)
    
    # 3. Schedule Drones dynamically across all paths
    scheduler = Scheduler(graph, paths)
    moves = scheduler.run()

    # 4. Format Output
    turns_dict = {}
    for turn, drone_id, target in moves:
        turns_dict.setdefault(turn, []).append(f"D{drone_id}-{target}")

    if turns_dict:
        max_turn = max(turns_dict.keys())
        for t in range(1, max_turn + 1):
            if t in turns_dict:
                # Sort by drone ID for clean output
                turn_moves = sorted(turns_dict[t], key=lambda x: int(x.split('-')[0][1:]))
                print(" ".join(turn_moves))

if __name__ == "__main__":
    main()
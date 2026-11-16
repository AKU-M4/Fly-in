*This project has been created as part of the 42 curriculum by [adkaid-s].*

# Fly-in

## Description

Fly-in is a Python simulation that routes a fleet of drones through a network of connected zones, from a single `start_hub` to a single `end_hub`, while respecting per-zone and per-connection capacity limits.

The program reads a text map describing zones (hubs), their coordinates, types, and capacities, along with the connections between them. It then computes, turn by turn, how every drone should move so that all drones reach the goal without ever exceeding a zone's or a connection's capacity at the same instant. No graph library (`networkx`, `graphlib`, etc.) is used: pathfinding, capacity-aware scheduling and map parsing are all implemented from scratch, and the whole codebase is fully typed and object-oriented.

At a high level, the project is split into four responsibilities:

- **Parsing** (`parser.py`, `parser_utils.py`, `models.py`, `exceptions.py`) — turns a raw map file into a validated, typed `Graph` object.
- **Pathfinding** (`router.py` – `PathFinder`) — finds several diversified shortest paths between the start and end hub.
- **Scheduling** (`router.py` – `Scheduler`, `ReservationTable`) — assigns each drone to the best available path and the exact turn at which it may enter each zone, so that capacities are never violated.
- **Presentation** (`main.py`) — runs the pipeline and prints the resulting turn-by-turn move list, color-coded by zone.

## Instructions

The project uses [`uv`](https://github.com/astral-sh/uv) for dependency management, and a `makefile` wraps the common commands.

### Requirements

- Python >= 3.10
- `uv` installed on your machine

### Install

```bash
make install
```

This runs `uv sync` and creates a local virtual environment with all dependencies (`pydantic`, `flake8`, `mypy`, `pygame`).

### Run

```bash
make run MAP=maps/easy/01_linear_path.txt
```

which is equivalent to:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

An optional `--capacity-info` flag can be appended to the command line to display additional information about zone/connection capacity while running.

### Debug

```bash
make debug
```

Runs the program under `pdb` on `maps/map_easy.txt`.

### Lint & type-check

```bash
make lint         # flake8 + mypy (relaxed profile)
make lint-strict   # flake8 + mypy --strict
```

### Clean

```bash
make clean
```

Removes `__pycache__`, `.mypy_cache`, `.pytest_cache` and `.venv`.

### Map files

Sample maps of increasing difficulty are provided in `maps/easy`, `maps/medium`, `maps/hard`, and `maps/challenger` (see `maps/README.md` for a full description of each map and what it is meant to test). A map file follows this structure:

```
nb_drones: <positive_integer>

start_hub: <name> <x> <y> [zone=<type> color=<color> max_drones=<n>]
hub: <name> <x> <y> [zone=<type> color=<color> max_drones=<n>]
end_hub: <name> <x> <y> [zone=<type> color=<color> max_drones=<n>]

connection: <zone1>-<zone2> [max_link_capacity=<n>]
```

`#` starts a comment (unless inside quotes), and metadata in `[...]` is optional.

## Algorithm choices & implementation strategy

**Parsing.** `MapParser` reads the map line by line, strips comments while respecting quoted strings, and extracts the optional `[key=value ...]` metadata block with a small hand-written scanner (no regex, so error locations and malformed-syntax cases stay easy to reason about). Each declaration is validated as it is read — duplicate zones, duplicate coordinates, duplicate `nb_drones`, unknown metadata keys, self-loops, duplicate connections, and isolated hubs are all rejected with a `MapParsingError` that carries the offending line number. Zones and connections are represented as `pydantic` models (`Zone`, `Connection`, `Graph` in `models.py`), which gives free, declarative validation (positive `max_drones`/`max_link_capacity`, valid zone names, etc.) on top of the parser's own checks.

**Pathfinding.** `PathFinder` computes several diversified shortest paths between `start_hub` and `end_hub` using a cost-based Dijkstra where the "cost" of entering a zone depends on its type (`normal`/`priority` cost 1, `restricted` costs 2, `blocked` is impassable). To obtain more than one usable path (useful for spreading drones across the network instead of funnelling everyone through the single shortest route), each time a path is found its edges receive a penalty before the search is run again — a lightweight, from-scratch alternative to Yen's k-shortest-paths idea, adapted to this project's constraint that no graph library may be used.

**Scheduling.** Because several drones can be in flight at once, a purely static shortest path is not enough: two drones could collide on the same zone or saturate the same connection at the same turn. `Scheduler` assigns drones one at a time (in ascending id order) and, for each drone, simulates every candidate path against a shared `ReservationTable` that tracks how many drones occupy each zone and each connection at every turn. The candidate path with the earliest arrival time under the current reservations is chosen, and its zone/connection usage is then booked for the turns it will occupy, before moving on to the next drone. This turns pathfinding + capacity constraints into a simple, deterministic time-expanded scheduling problem without needing a full multi-agent path-finding solver.

**Output.** `main.py` turns the list of `(turn, drone_id, target)` moves produced by the scheduler into the turn-by-turn textual output the 42 subject expects, grouping and sorting moves by turn and by drone id.

## Visual representation

Terminal output is color-coded using ANSI escape codes: each zone's declared `color` metadata (e.g. `green` for the start hub, `red` for the goal, or any custom color used to mark bottlenecks, restricted zones, priority zones, etc.) is rendered directly around the zone's name in the move list. This makes it possible to scan a run at a glance and immediately spot which drones are passing through bottlenecks, restricted zones, or the goal, without having to cross-reference the move list against the map file.

## Example

Given `maps/easy/01_linear_path.txt`:

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Running:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

produces (colors omitted here, but rendered in a real terminal — `waypoint1`/`waypoint2` appear in blue, `goal` in red):

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line is one simulation turn; each `D<id>-<zone>` entry means drone `<id>` is now in `<zone>` (or crossing the connection towards it, for 2-turn `restricted` zones).

## Resources

### References

- [Dijkstra's algorithm (Wikipedia)](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) — base shortest-path algorithm adapted for `PathFinder`.
- [Yen's algorithm for k-shortest loopless paths (Wikipedia)](https://en.wikipedia.org/wiki/Yen%27s_algorithm) — conceptual inspiration for generating several diversified paths through edge penalties.
- [Time-expanded graphs / Conflict-Based Search for multi-agent pathfinding](https://en.wikipedia.org/wiki/Multi-agent_pathfinding) — general background on the class of problem the capacity-aware scheduler solves.
- [Pydantic documentation](https://docs.pydantic.dev/) — used for the typed, self-validating `Zone`, `Connection`, and `Graph` models.
- [mypy documentation](https://mypy.readthedocs.io/) and [flake8 documentation](https://flake8.pycqa.org/) — used to keep the codebase fully typed and PEP8-compliant, as required by the subject.

### AI usage

AI assistance (Claude) was used in a supporting, non-authoring role on this project:

- **Project structure**: discussing how to split the codebase into clear responsibilities (`models.py` for typed data, `parser.py`/`parser_utils.py` for map parsing, `router.py` for pathfinding and scheduling, `main.py` for the CLI/presentation layer) so the code stays object-oriented and each module has a single, testable purpose, in line with the subject's requirements.
- **Code review for redundancy**: identifying that `parser_utils.py`'s `MetadataParser.extract_and_parse` duplicated logic already implemented (and more strictly validated) inside `MapParser` in `parser.py`, and was not actually called anywhere in the codebase — flagged as dead/redundant parsing code to simplify or remove.
- **Type-checking help**: helping track down and resolve `mypy --strict` violations (missing/incorrect annotations, `Optional` handling around `start_hub`/`end_hub`, and typed collections in `router.py` and `main.py`) so the project passes both `make lint` and `make lint-strict` cleanly.

All algorithmic logic, the parsing grammar, the scheduling strategy and the final code were written and validated by the author; AI was used for guidance, review, and debugging rather than to generate the solution itself.

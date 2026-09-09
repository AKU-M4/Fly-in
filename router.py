import heapq
from typing import Dict, List, Tuple
from models import Graph, ZoneType


class ReservationTable:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.node_traffic: Dict[Tuple[str, int], int] = {}
        self.edge_traffic: Dict[Tuple[Tuple[str, str], int], int] = {}

    def get_edge_key(self, u: str, v: str) -> Tuple[str, str]:
        return (min(u, v), max(u, v))

    def get_edge_capacity(self, u: str, v: str) -> int:
        key = self.get_edge_key(u, v)
        for conn in self.graph.connections:
            if self.get_edge_key(conn.zone1_name, conn.zone2_name) == key:
                return conn.max_link_capacity
        return 1

    def is_edge_free(self, u: str, v: str, dep_t: int, cost: int) -> bool:
        cap = self.get_edge_capacity(u, v)
        key = self.get_edge_key(u, v)
        for t in range(dep_t, dep_t + cost):
            if self.edge_traffic.get((key, t), 0) >= cap:
                return False
        return True

    def book_edge(self, u: str, v: str, dep_t: int, cost: int) -> None:
        key = self.get_edge_key(u, v)
        for t in range(dep_t, dep_t + cost):
            self.edge_traffic[(key, t)] = (
                self.edge_traffic.get((key, t), 0) + 1
            )

    def is_node_free(self, z_name: str, turn: int) -> bool:
        start_name = (
            self.graph.start_hub.name if self.graph.start_hub else None
        )
        end_name = (
            self.graph.end_hub.name if self.graph.end_hub else None
        )
        if z_name in (start_name, end_name):
            return True

        limit = self.graph.zones[z_name].max_drones
        current = self.node_traffic.get((z_name, turn), 0)
        return bool(limit > current)

    def book_node(self, z_name: str, turn: int) -> None:
        start_name = (
            self.graph.start_hub.name if self.graph.start_hub else None
        )
        end_name = (
            self.graph.end_hub.name if self.graph.end_hub else None
        )
        if z_name not in (start_name, end_name):
            key = (z_name, turn)
            self.node_traffic[key] = self.node_traffic.get(key, 0) + 1


class PathFinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def get_k_paths(self, k: int = 5) -> List[List[str]]:
        if not self.graph.start_hub or not self.graph.end_hub:
            return []

        start = self.graph.start_hub.name
        end = self.graph.end_hub.name
        paths: List[List[str]] = []
        edge_penalties: Dict[Tuple[str, str], int] = {}

        for _ in range(k):
            path = self._djikstra(start, end, edge_penalties)
            if not path or path in paths:
                break
            paths.append(path)

            for i in range(len(path) - 1):
                pair = (
                    min(path[i], path[i + 1]),
                    max(path[i], path[i + 1]),
                )
                edge_penalties[pair] = edge_penalties.get(pair, 0) + 5

        return paths

    def _djikstra(
        self,
        start: str,
        end: str,
        penalties: Dict[Tuple[str, str], int],
    ) -> List[str]:
        pq: List[Tuple[int, str, List[str]]] = [(0, start, [start])]
        best_costs: Dict[str, float] = {start: 0.0}

        while pq:
            cost, current, path = heapq.heappop(pq)

            if current == end:
                return path

            if cost > best_costs.get(current, float("inf")):
                continue

            for conn in self.graph.adj_list.get(current, []):
                if conn.zone1_name == current:
                    neighbor = conn.zone2_name
                else:
                    neighbor = conn.zone1_name

                neighbor_zone = self.graph.zones[neighbor]

                if neighbor_zone.zone_type == ZoneType.BLOCKED:
                    continue

                step_cost = neighbor_zone.travel_cost
                pair = (min(current, neighbor), max(current, neighbor))
                total_cost = cost + step_cost + penalties.get(pair, 0)

                if total_cost < best_costs.get(neighbor, float("inf")):
                    best_costs[neighbor] = float(total_cost)
                    heapq.heappush(
                        pq, (total_cost, neighbor, path + [neighbor])
                    )
        return []


class Scheduler:
    def __init__(self, graph: Graph, paths: List[List[str]]) -> None:
        self.graph = graph
        self.paths = paths
        self.table = ReservationTable(graph)
        self.all_moves: List[Tuple[int, int, str]] = []

    def run(self) -> List[Tuple[int, int, str]]:
        all_moves: List[Tuple[int, int, str]] = []

        for drone_id in range(1, self.graph.nb_drones + 1):
            best_arrival = float("inf")
            best_moves: List[Tuple[int, int, str]] = []
            best_reservations: List[Tuple[str, str, int, int]] = []

            for path in self.paths:
                arrival, moves, reservations = self._simulate_path(
                    drone_id, path
                )
                if arrival < best_arrival:
                    best_arrival = float(arrival)
                    best_moves = moves
                    best_reservations = reservations

            for curr_room, next_room, dep_t, arr_t in best_reservations:
                cost = arr_t - dep_t
                self.table.book_edge(curr_room, next_room, dep_t, cost)
                dest_turn = dep_t if cost == 1 else dep_t + 1
                self.table.book_node(next_room, dest_turn)

            all_moves.extend(best_moves)

        self.all_moves = all_moves
        return all_moves

    def _simulate_path(
        self,
        drone_id: int,
        path: List[str],
    ) -> Tuple[
        int,
        List[Tuple[int, int, str]],
        List[Tuple[str, str, int, int]],
    ]:
        moves: List[Tuple[int, int, str]] = []
        reservations: List[Tuple[str, str, int, int]] = []
        curr_turn = 1

        for i in range(len(path) - 1):
            curr_room = path[i]
            next_room = path[i + 1]

            cost = self.graph.zones[next_room].travel_cost

            while True:
                edge_free = self.table.is_edge_free(
                    curr_room, next_room, curr_turn, cost
                )
                dest_turn = curr_turn if cost == 1 else curr_turn + 1
                dest_free = self.table.is_node_free(next_room, dest_turn)

                if edge_free and dest_free:
                    break
                curr_turn += 1

            arrival_turn = curr_turn + cost
            reservations.append(
                (curr_room, next_room, curr_turn, arrival_turn)
            )

            if cost == 2:
                moves.append(
                    (curr_turn, drone_id, f"{curr_room}-{next_room}")
                )
                moves.append(
                    (curr_turn + 1, drone_id, next_room)
                )
            else:
                moves.append((curr_turn, drone_id, next_room))

            curr_turn = arrival_turn

        return curr_turn, moves, reservations

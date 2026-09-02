import heapq
from dataclasses import dataclass
from typing import Dict, List, Tuple
from src.models import Graph, Zone, ZoneType


@dataclass
class MoveStep:
    turn: int
    drone_id: int
    target_name: str
    is_connection: bool = False


class PathFinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def find_k_paths(self, k: int = 5) -> List[List[str]]:
        if not self.graph.start_hub or not self.graph.end_hub:
            return []

        start_name = self.graph.start_hub.name
        end_name = self.graph.end_hub.name
        paths: List[List[str]] = []
        edge_penalties: Dict[Tuple[str, str], int] = {}

        for _ in range(k):
            path = self._dijkstra(start_name, end_name, edge_penalties)
            if not path or path in paths:
                break
            paths.append(path)

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                pair = (min(u, v), max(u, v))
                edge_penalties[pair] = edge_penalties.get(pair, 0) + 3

        return paths

    def _dijkstra(self, start: str, end: str, penalties: Dict[Tuple[str, str], int]) -> List[str]:
        pq: List[Tuple[int, str, List[str]]] = [(0, start, [start])]
        visited_costs: Dict[str, int] = {start: 0}

        while pq:
            cost, current, path = heapq.heappop(pq)

            if current == end:
                return path

            if cost > visited_costs.get(current, float("inf")):
                continue

            for conn in self.graph.adj_list.get(current, []):
                neighbor_name = conn.zone2_name if conn.zone1_name == current else conn.zone1_name
                neighbor_zone = self.graph.zones[neighbor_name]

                if neighbor_zone.zone_type == ZoneType.BLOCKED:
                    continue

                edge_cost = neighbor_zone.travel_cost
                if neighbor_zone.zone_type == ZoneType.PRIORITY:
                    edge_cost = max(1, edge_cost - 1)

                edge_pair = (min(current, neighbor_name), max(current, neighbor_name))
                total_step_cost = edge_cost + penalties.get(edge_pair, 0)

                new_cost = cost + total_step_cost
                if new_cost < visited_costs.get(neighbor_name, float("inf")):
                    visited_costs[neighbor_name] = new_cost
                    heapq.heappush(pq, (new_cost, neighbor_name, path + [neighbor_name]))

        return []


class TimeSpaceScheduler:
    def __init__(self, graph: Graph, candidate_paths: List[List[str]]) -> None:
        self.graph = graph
        self.paths = candidate_paths
        self.node_occupancy: Dict[int, Dict[str, int]] = {}
        self.edge_occupancy: Dict[int, Dict[Tuple[str, str], int]] = {}

    def schedule_all_drones(self) -> Dict[int, List[MoveStep]]:
        turn_movements: Dict[int, List[MoveStep]] = {}

        for drone_id in range(1, self.graph.nb_drones + 1):
            best_schedule: List[MoveStep] = []
            best_arrival_turn = float("inf")

            for path in self.paths:
                schedule, arrival_turn = self._try_schedule_drone(drone_id, path)
                if arrival_turn < best_arrival_turn:
                    best_arrival_turn = arrival_turn
                    best_schedule = schedule

            self._commit_schedule(best_schedule)

            for step in best_schedule:
                turn_movements.setdefault(step.turn, []).append(step)

        return turn_movements

    def _try_schedule_drone(self, drone_id: int, path: List[str]) -> Tuple[List[MoveStep], int]:
        schedule: List[MoveStep] = []
        current_turn = 1

        for i in range(len(path) - 1):
            curr_zone = self.graph.zones[path[i]]
            next_zone = self.graph.zones[path[i + 1]]
            edge_pair = (min(curr_zone.name, next_zone.name), max(curr_zone.name, next_zone.name))

            while True:
                cost = next_zone.travel_cost

                if not self._can_traverse_edge(edge_pair, current_turn):
                    current_turn += 1
                    continue

                if not self._can_occupy_zone(next_zone, current_turn + cost):
                    current_turn += 1
                    continue

                break

            if cost == 2:
                conn_name = f"{curr_zone.name}-{next_zone.name}"
                schedule.append(
                    MoveStep(turn=current_turn, drone_id=drone_id, target_name=conn_name, is_connection=True)
                )
                schedule.append(
                    MoveStep(turn=current_turn + 1, drone_id=drone_id, target_name=next_zone.name)
                )
            else:
                schedule.append(
                    MoveStep(turn=current_turn, drone_id=drone_id, target_name=next_zone.name)
                )

            current_turn += cost

        return schedule, current_turn

    def _can_occupy_zone(self, zone: Zone, turn: int) -> bool:
        if zone == self.graph.start_hub or zone == self.graph.end_hub:
            return True
        current_count = self.node_occupancy.get(turn, {}).get(zone.name, 0)
        return current_count < zone.max_drones

    def _can_traverse_edge(self, edge_pair: Tuple[str, str], turn: int) -> bool:
        max_cap = 1
        for conn in self.graph.connections:
            if (min(conn.zone1_name, conn.zone2_name), max(conn.zone1_name, conn.zone2_name)) == edge_pair:
                max_cap = conn.max_link_capacity
                break
        current_count = self.edge_occupancy.get(turn, {}).get(edge_pair, 0)
        return current_count < max_cap

    def _commit_schedule(self, schedule: List[MoveStep]) -> None:
        for step in schedule:
            if not step.is_connection:
                self.node_occupancy.setdefault(step.turn, {})
                self.node_occupancy[step.turn][step.target_name] = (
                    self.node_occupancy[step.turn].get(step.target_name, 0) + 1
                )

from typing import Dict, List, Optional, Set, Tuple
from src.models import Graph
from src.router import MoveStep


class Visualizer:
    COLOR_PALETTE: Dict[str, Tuple[int, int, int]] = {
        "red": (235, 77, 75),
        "green": (46, 204, 113),
        "yellow": (241, 196, 15),
        "blue": (52, 152, 219),
        "purple": (155, 89, 182),
        "magenta": (155, 89, 182),
        "gray": (127, 140, 141),
        "white": (236, 240, 241),
        "dark": (30, 30, 46),
        "line": (88, 91, 112),
        "drone": (243, 139, 168),
    }

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def render_terminal(self, turn_movements: Dict[int, List[MoveStep]]) -> None:
        """Outputs standard format lines to stdout turn-by-turn."""
        max_turn = max(turn_movements.keys()) if turn_movements else 0
        for turn in range(1, max_turn + 1):
            steps = turn_movements.get(turn, [])
            if not steps:
                continue
            tokens = [f"D{s.drone_id}-{s.target_name}" for s in steps]
            print(" ".join(tokens))

    def render_gui(
        self,
        turn_movements: Dict[int, List[MoveStep]],
        width: int = 1000,
        height: int = 750,
        turn_delay_ms: int = 700,
    ) -> None:
        """Renders an interactive 2D graph window using Pygame."""
        try:
            import pygame
        except ImportError:
            print("Error: pygame is not installed. Run 'uv add pygame'.")
            self.render_terminal(turn_movements)
            return

        pygame.init()
        pygame.font.init()

        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fly-in Graph Visualizer")
        clock = pygame.time.Clock()

        font_small = pygame.font.SysFont("monospace", 13, bold=True)
        font_title = pygame.font.SysFont("monospace", 18, bold=True)

        # Scale graph coordinates to window
        xs = [z.x for z in self.graph.zones.values()]
        ys = [z.y for z in self.graph.zones.values()]
        min_x, max_x = (min(xs), max(xs)) if xs else (0, 1)
        min_y, max_y = (min(ys), max(ys)) if ys else (0, 1)

        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)

        pad_x, pad_y = 100, 100
        draw_w = width - 2 * pad_x
        draw_h = height - 2 * pad_y

        screen_coords: Dict[str, Tuple[int, int]] = {}
        for name, zone in self.graph.zones.items():
            sx = int(pad_x + ((zone.x - min_x) / span_x) * draw_w)
            sy = int(height - (pad_y + ((zone.y - min_y) / span_y) * draw_h))
            screen_coords[name] = (sx, sy)

        max_turn = max(turn_movements.keys()) if turn_movements else 0
        current_turn = 0
        paused = False
        last_turn_time = pygame.time.get_ticks()

        drone_positions: Dict[int, str] = {
            d: self.graph.start_hub.name
            for d in range(1, self.graph.nb_drones + 1)
            if self.graph.start_hub
        }

        def advance_turn() -> None:
            nonlocal current_turn
            if current_turn < max_turn:
                current_turn += 1
                for step in turn_movements.get(current_turn, []):
                    drone_positions[step.drone_id] = step.target_name

        def reset_sim() -> None:
            nonlocal current_turn
            current_turn = 0
            for d in range(1, self.graph.nb_drones + 1):
                if self.graph.start_hub:
                    drone_positions[d] = self.graph.start_hub.name

        def get_color(cname: Optional[str]) -> Tuple[int, int, int]:
            if not cname:
                return self.COLOR_PALETTE["white"]
            return self.COLOR_PALETTE.get(cname.lower(), self.COLOR_PALETTE["white"])

        running = True
        while running:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_RIGHT:
                        advance_turn()
                    elif event.key == pygame.K_r:
                        reset_sim()

            if not paused and current_turn < max_turn:
                if now - last_turn_time >= turn_delay_ms:
                    advance_turn()
                    last_turn_time = now

            # Draw canvas
            screen.fill(self.COLOR_PALETTE["dark"])

            # 1. Draw connections
            seen: Set[Tuple[str, str]] = set()
            for conn in self.graph.connections:
                pair = (min(conn.zone1_name, conn.zone2_name), max(conn.zone1_name, conn.zone2_name))
                if pair in seen:
                    continue
                seen.add(pair)
                p1, p2 = screen_coords[conn.zone1_name], screen_coords[conn.zone2_name]
                pygame.draw.line(screen, self.COLOR_PALETTE["line"], p1, p2, 2)

            # 2. Draw nodes
            radius = 20
            for name, zone in self.graph.zones.items():
                pos = screen_coords[name]
                fill_color = get_color(zone.color)

                border_color = (255, 255, 255)
                border_width = 2
                if zone == self.graph.start_hub:
                    border_color = self.COLOR_PALETTE["green"]
                    border_width = 4
                elif zone == self.graph.end_hub:
                    border_color = self.COLOR_PALETTE["red"]
                    border_width = 4

                pygame.draw.circle(screen, fill_color, pos, radius)
                pygame.draw.circle(screen, border_color, pos, radius, border_width)

                tag = font_small.render(name, True, (205, 214, 244))
                screen.blit(tag, (pos[0] - tag.get_width() // 2, pos[1] + radius + 5))

            # 3. Draw drones
            grouped: Dict[str, List[int]] = {}
            for d_id, loc in drone_positions.items():
                grouped.setdefault(loc, []).append(d_id)

            for loc, drones in grouped.items():
                d_text = ",".join(f"D{d}" for d in drones)
                surf = font_small.render(d_text, True, (17, 17, 27))
                bw, bh = surf.get_width() + 10, surf.get_height() + 4

                if loc in screen_coords:
                    cx, cy = screen_coords[loc]
                    rect = pygame.Rect(cx - bw // 2, cy - 38, bw, bh)
                elif "-" in loc:
                    u, v = loc.split("-", 1)
                    if u in screen_coords and v in screen_coords:
                        p1, p2 = screen_coords[u], screen_coords[v]
                        rect = pygame.Rect((p1[0] + p2[0]) // 2 - bw // 2, (p1[1] + p2[1]) // 2 - bh // 2, bw, bh)
                    else:
                        continue
                else:
                    continue

                pygame.draw.rect(screen, self.COLOR_PALETTE["drone"], rect, border_radius=4)
                screen.blit(surf, (rect.x + 5, rect.y + 2))

            # 4. Header UI
            steps = turn_movements.get(current_turn, [])
            move_str = " ".join(f"D{s.drone_id}-{s.target_name}" for s in steps)
            state_str = "[PAUSED]" if paused else "[RUNNING]"
            hdr = font_title.render(
                f"Turn {current_turn:02d}/{max_turn:02d} {state_str} | Moves: {move_str or 'Standby'}",
                True,
                (248, 248, 242),
            )
            screen.blit(hdr, (20, 20))

            sub = font_small.render("[SPACE] Pause/Play  [→] Step  [R] Reset", True, (147, 153, 178))
            screen.blit(sub, (20, 48))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

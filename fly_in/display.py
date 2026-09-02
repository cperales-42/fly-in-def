import math
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .zone import Zone
from .connection import Connection
from .drone import Drone
from .orchestrator import Orchestrator


class Grid:
    rainbow_colors: tuple[tuple[int, int, int], ...] = (
        (255, 0, 0),
        (255, 127, 0),
        (255, 255, 0),
        (0, 255, 0),
        (0, 127, 255),
        (75, 0, 130),
        (148, 0, 211),
    )

    def __init__(
        self,
        zones: list[Zone],
        connections: list[Connection],
        screen_size: tuple[int, int],
        margin: int = 100,
        node_size_ratio: float = 0.6,
    ):
        self.zones = zones
        self.connections = connections

        self.screen_width, self.screen_height = screen_size
        self.margin = margin
        self.node_size_ratio = node_size_ratio

        self.coordinates = {
            zone.get_coordinates()
            for zone in zones
        }

        self.animation_duration = 0.35

        self._calculate_transform()

        self.visual_zone_drones: dict[
            Zone,
            list[Drone],
        ] = {}

        for zone in self.zones:
            self.visual_zone_drones[zone] = (
                list(zone.get_drones())
            )


        self.visual_connection_drones: dict[
            Connection,
            list[Drone],
        ] = {}

        for connection in self.connections:
            self.visual_connection_drones[connection] = (
                list(connection.get_drones())
            )

        self.animating_drone: Drone | None = None

        self.animating_start: tuple[
            float,
            float,
        ] | None = None

        self.animating_end: tuple[
            float,
            float,
        ] | None = None

        self.animating_progress = 0.0

    def _calculate_transform(self) -> None:

        if not self.coordinates:
            self.scale = 1
            self.offset_x = self.screen_width / 2
            self.offset_y = self.screen_height / 2
            self.node_radius = 30
            self.transform_min_x = 0
            self.transform_min_y = 0
            self.transform_width = 0
            self.transform_height = 0
            return

        xs = [
            x
            for x, _ in self.coordinates
        ]

        ys = [
            y
            for _, y in self.coordinates
        ]

        min_x = min(xs)
        max_x = max(xs)

        min_y = min(ys)
        max_y = max(ys)

        grid_width = max_x - min_x
        grid_height = max_y - min_y

        self.transform_min_x = min_x
        self.transform_min_y = min_y
        self.transform_width = grid_width
        self.transform_height = grid_height

        available_width = (
            self.screen_width
            - self.margin * 2
        )

        available_height = (
            self.screen_height
            - self.margin * 2
        )

        scale_x = (
            available_width / grid_width
            if grid_width > 0
            else available_width
        )

        scale_y = (
            available_height / grid_height
            if grid_height > 0
            else available_height
        )

        self.scale = min(
            scale_x,
            scale_y,
        )

        center_x = (
            min_x + max_x
        ) / 2

        center_y = (
            min_y + max_y
        ) / 2

        self.offset_x = (
            self.screen_width / 2
            - center_x * self.scale
        )

        self.offset_y = (
            self.screen_height / 2
            - center_y * self.scale
        )

        self.node_radius = (
            self.scale
            * self.node_size_ratio
            / 2
        )

        self.node_radius = max(
            self.node_radius,
            15,
        )

    def grid_to_screen(
        self,
        coordinate: tuple[int, int],
    ) -> tuple[int, int]:

        x, y = coordinate

        if self.transform_width > 0:
            horizontal_ratio = (
                (2 * (x - self.transform_min_x) - self.transform_width)
                / (2 * self.transform_width)
            )
        else:
            horizontal_ratio = 0

        if self.transform_height > 0:
            vertical_ratio = (
                (2 * (y - self.transform_min_y) - self.transform_height)
                / (2 * self.transform_height)
            )
        else:
            vertical_ratio = 0

        return (
            int(self.screen_width / 2 + horizontal_ratio * self.scale * self.transform_width),
            int(self.screen_height / 2 + vertical_ratio * self.scale * self.transform_height),
        )

    def get_node_radius(self) -> int:
        return int(self.node_radius)

    def _get_zone_center(
        self,
        zone: Zone,
    ) -> tuple[int, int]:

        return self.grid_to_screen(
            zone.get_coordinates()
        )

    def _get_connection_center(
        self,
        connection: Connection,
    ) -> tuple[int, int]:
        z1 = connection.get_zone_1()
        z2 = connection.get_zone_2()
        c1 = self._get_zone_center(z1)
        c2 = self._get_zone_center(z2)
        return (
            (c1[0] + c2[0]) // 2,
            (c1[1] + c2[1]) // 2,
        )

    def _split_name(
        self,
        name: str,
        max_width: int,
        font: pygame.font.Font,
    ) -> list[str]:

        words = name.split()

        if not words:
            return [""]

        lines = []
        current = ""

        for word in words:

            test = (
                word
                if not current
                else current + " " + word
            )

            if font.size(test)[0] <= max_width:
                current = test

            else:

                if current:
                    lines.append(current)

                current = word

        if current:
            lines.append(current)

        final_lines = []

        for line in lines:

            if font.size(line)[0] <= max_width:
                final_lines.append(line)
                continue

            current = ""

            for char in line:

                test = current + char

                if font.size(test)[0] <= max_width:
                    current = test

                else:

                    if current:
                        final_lines.append(current)

                    current = char

            if current:
                final_lines.append(current)

        return final_lines

    def _draw_zone_name(
        self,
        screen: pygame.Surface,
        zone: Zone,
        center: tuple[int, int],
    ) -> None:

        radius = self.get_node_radius()

        font_size = max(
            int(radius * 0.32),
            10,
        )

        font = pygame.font.SysFont(
            "arial",
            font_size,
            bold=True,
        )

        max_width = int(
            radius * 1.7
        )

        lines = self._split_name(
            zone.get_name(),
            max_width,
            font,
        )

        line_height = font.get_linesize()

        total_height = (
            len(lines)
            * line_height
        )

        start_y = (
            center[1]
            - total_height / 2
        )

        for i, line in enumerate(lines):

            surface = font.render(
                line,
                True,
                "black",
            )

            rect = surface.get_rect(
                center=(
                    center[0],
                    int(
                        start_y
                        + i * line_height
                        + line_height / 2
                    ),
                )
            )

            screen.blit(
                surface,
                rect,
            )

    def _draw_drone(
        self,
        screen: pygame.Surface,
        position: tuple[float, float],
        drone: Drone,
    ) -> None:

        radius = self.get_node_radius()

        size = max(
            int(radius * 0.35),
            8,
        )

        rect = pygame.Rect(
            int(
                position[0]
                - size / 2
            ),
            int(
                position[1]
                - size / 2
            ),
            size,
            size,
        )

        pygame.draw.rect(
            screen,
            "white",
            rect,
        )

        pygame.draw.rect(
            screen,
            "black",
            rect,
            1,
        )

        font_size = max(
            int(size * 0.60),
            7,
        )

        font = pygame.font.SysFont(
            "arial",
            font_size,
            bold=True,
        )

        text = font.render(
            f"D{drone.get_index()}",
            True,
            "black",
        )

        text_rect = text.get_rect(
            center=rect.center
        )

        screen.blit(
            text,
            text_rect,
        )

    def _draw_zone_drones(
        self,
        screen: pygame.Surface,
        zone: Zone,
    ) -> None:

        drones = self.visual_zone_drones.get(
            zone,
            [],
        )

        if not drones:
            return

        center = self._get_zone_center(
            zone
        )

        drone = max(
            drones,
            key=lambda d: d.get_index(),
        )

        self._draw_drone(
            screen,
            center,
            drone,
        )

    def _draw_connection_drones(
        self,
        screen: pygame.Surface,
        connection: Connection,
    ) -> None:
        drones = self.visual_connection_drones.get(
            connection,
            [],
        )

        if not drones:
            return

        center = self._get_connection_center(
            connection
        )

        drone = max(
            drones,
            key=lambda d: d.get_index(),
        )

        self._draw_drone(
            screen,
            center,
            drone,
        )

    def _draw_arrow(
        self,
        screen: pygame.Surface,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> None:

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        distance = math.hypot(
            dx,
            dy,
        )

        if distance == 0:
            return

        ux = dx / distance
        uy = dy / distance

        radius = self.get_node_radius()

        start_offset = radius + 5
        end_offset = radius + 10

        line_start = (
            int(
                start[0]
                + ux * start_offset
            ),
            int(
                start[1]
                + uy * start_offset
            ),
        )

        line_end = (
            int(
                end[0]
                - ux * end_offset
            ),
            int(
                end[1]
                - uy * end_offset
            ),
        )

        pygame.draw.line(
            screen,
            (80, 80, 80),
            line_start,
            line_end,
            3,
        )

        arrow_size = 12

        perpendicular = (
            -uy,
            ux,
        )

        p1 = line_end

        p2 = (
            int(
                line_end[0]
                - ux * arrow_size
                + perpendicular[0]
                * arrow_size
                * 0.5
            ),
            int(
                line_end[1]
                - uy * arrow_size
                + perpendicular[1]
                * arrow_size
                * 0.5
            ),
        )

        p3 = (
            int(
                line_end[0]
                - ux * arrow_size
                - perpendicular[0]
                * arrow_size
                * 0.5
            ),
            int(
                line_end[1]
                - uy * arrow_size
                - perpendicular[1]
                * arrow_size
                * 0.5
            ),
        )

        pygame.draw.polygon(
            screen,
            (80, 80, 80),
            [p1, p2, p3],
        )

        reverse_line_end = line_start
        reverse_p1 = reverse_line_end
        reverse_p2 = (
            int(
                reverse_line_end[0]
                + ux * arrow_size
                + perpendicular[0] * arrow_size * 0.5
            ),
            int(
                reverse_line_end[1]
                + uy * arrow_size
                + perpendicular[1] * arrow_size * 0.5
            ),
        )
        reverse_p3 = (
            int(
                reverse_line_end[0]
                + ux * arrow_size
                - perpendicular[0] * arrow_size * 0.5
            ),
            int(
                reverse_line_end[1]
                + uy * arrow_size
                - perpendicular[1] * arrow_size * 0.5
            ),
        )
        pygame.draw.polygon(
            screen,
            (80, 80, 80),
            [reverse_p1, reverse_p2, reverse_p3],
        )

    def _draw_connections(
        self,
        screen: pygame.Surface,
    ) -> None:

        for connection in self.connections:

            zone1 = connection.get_zone_1()
            zone2 = connection.get_zone_2()

            start = self._get_zone_center(
                zone1
            )

            end = self._get_zone_center(
                zone2
            )

            self._draw_arrow(
                screen,
                start,
                end,
            )

            self._draw_connection_drones(
                screen,
                connection,
            )

    def _get_zone_color(self, zone: Zone) -> str | tuple[int, int, int]:
        color = zone.get_color()
        if color.lower() != "rainbow":
            return color
        color_index = (
            pygame.time.get_ticks() // 300
        ) % len(self.rainbow_colors)
        return self.rainbow_colors[color_index]

    def _draw_zones(
        self,
        screen: pygame.Surface,
    ) -> None:

        for zone in self.zones:

            center = self._get_zone_center(
                zone
            )

            radius = self.get_node_radius()

            pygame.draw.circle(
                screen,
                self._get_zone_color(zone),
                center,
                radius,
            )

            pygame.draw.circle(
                screen,
                "black",
                center,
                radius,
                2,
            )

            self._draw_zone_name(
                screen,
                zone,
                center,
            )

            self._draw_zone_drones(
                screen,
                zone,
            )

    def draw(
        self,
        screen: pygame.Surface,
    ) -> None:

        self._draw_connections(screen)

        self._draw_zones(screen)

        if (
            self.animating_drone is not None
            and
            self.animating_start is not None
            and
            self.animating_end is not None
        ):

            start = self.animating_start
            end = self.animating_end

            p = self.animating_progress

            x = (
                start[0]
                + (end[0] - start[0]) * p
            )

            y = (
                start[1]
                + (end[1] - start[1]) * p
            )

            self._draw_drone(
                screen,
                (x, y),
                self.animating_drone,
            )

    def _find_movement(self):
        real_zone_drones = {
            z: {
                d.get_index()
                for d in z.get_drones()
            }
            for z in self.zones
        }
        real_conn_drones = {
            c: {
                d.get_index()
                for d in c.get_drones()
            }
            for c in self.connections
        }


        for zone in reversed(self.zones):
            v_drones = self.visual_zone_drones.get(
                zone,
                [],
            )
            for drone in v_drones:
                d_idx = drone.get_index()
                current_loc = None
                is_zone = True

                for z, r_indices in real_zone_drones.items():
                    if d_idx in r_indices:
                        current_loc = z
                        break

                if current_loc is None:
                    for c, r_indices in real_conn_drones.items():
                        if d_idx in r_indices:
                            current_loc = c
                            is_zone = False
                            break

                if current_loc and (current_loc != zone or not is_zone):
                    return (drone, zone, current_loc)


        for conn in self.connections:
            v_drones = self.visual_connection_drones.get(
                conn,
                [],
            )
            for drone in v_drones:
                d_idx = drone.get_index()
                current_loc = None
                is_zone = True

                for z, r_indices in real_zone_drones.items():
                    if d_idx in r_indices:
                        current_loc = z
                        break

                if current_loc is None:
                    for c, r_indices in real_conn_drones.items():
                        if d_idx in r_indices:
                            current_loc = c
                            is_zone = False
                            break

                if current_loc and (current_loc != conn or is_zone):
                    return (drone, conn, current_loc)

        return None

    def animate_changes(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
    ) -> None:

        while True:

            movement = self._find_movement()

            if movement is None:
                break

            drone, origin_obj, dest_obj = movement


            if isinstance(origin_obj, Zone):
                start = self._get_zone_center(origin_obj)
            else:
                start = self._get_connection_center(origin_obj)


            if isinstance(dest_obj, Zone):
                end = self._get_zone_center(dest_obj)
            else:
                end = self._get_connection_center(dest_obj)

            self.animating_drone = drone
            self.animating_start = start
            self.animating_end = end
            self.animating_progress = 0.0

            screen.fill(
                (200, 200, 200)
            )

            self.draw(screen)

            pygame.display.flip()

            self._animate_drone(
                screen,
                clock,
            )


            if isinstance(origin_obj, Zone):
                if drone in self.visual_zone_drones[origin_obj]:
                    self.visual_zone_drones[origin_obj].remove(drone)
            else:
                if drone in self.visual_connection_drones[origin_obj]:
                    self.visual_connection_drones[origin_obj].remove(drone)


            if isinstance(dest_obj, Zone):
                if dest_obj not in self.visual_zone_drones:
                    self.visual_zone_drones[dest_obj] = []
                if drone not in self.visual_zone_drones[dest_obj]:
                    self.visual_zone_drones[dest_obj].append(drone)
            else:
                if dest_obj not in self.visual_connection_drones:
                    self.visual_connection_drones[dest_obj] = []
                if drone not in self.visual_connection_drones[dest_obj]:
                    self.visual_connection_drones[dest_obj].append(drone)

            self.animating_drone = None
            self.animating_start = None
            self.animating_end = None
            self.animating_progress = 0.0

            screen.fill(
                (200, 200, 200)
            )

            self.draw(screen)

            pygame.display.flip()

    def _animate_drone(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
    ) -> None:

        start_time = pygame.time.get_ticks()

        running = True

        while running:

            now = pygame.time.get_ticks()

            elapsed = (
                now - start_time
            ) / 1000.0

            progress = (
                elapsed
                / self.animation_duration
            )

            if progress >= 1.0:

                progress = 1.0
                running = False

            smooth = (
                progress
                * progress
                * (3 - 2 * progress)
            )

            self.animating_progress = smooth

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    raise SystemExit

            screen.fill(
                (200, 200, 200)
            )

            self.draw(screen)

            pygame.display.flip()

            clock.tick(60)

        self.animating_progress = 1.0


def show_initial_state(
    o: Orchestrator,
    grid: Grid,
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    seconds: float = 2.0,
) -> None:

    start_time = pygame.time.get_ticks()

    while (
        pygame.time.get_ticks() - start_time
    ) < seconds * 1000:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        screen.fill((200, 200, 200))

        grid.draw(screen)

        pygame.display.flip()

        clock.tick(60)


def init_display(o: Orchestrator):
    pygame.init()

    WIDTH = 1920
    HEIGHT = 1080

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    pygame.display.set_caption("Fly-in")

    clock = pygame.time.Clock()

    grid = Grid(
        zones=o.get_zones(),
        connections=o.get_connections(),
        screen_size=(WIDTH, HEIGHT),
    )

    return screen, clock, grid


def display(
    o: Orchestrator,
    screen: pygame.Surface,
    grid: Grid,
) -> None:
    screen.fill((200, 200, 200))
    grid.draw(screen)
    pygame.display.flip()

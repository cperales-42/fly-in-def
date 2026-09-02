from .zone import Zone
from .connection import Connection
from .orchestrator import Orchestrator
from .display import init_display, show_initial_state
from collections import deque
import copy

def basic_test(o: Orchestrator) -> None:
    start = o.get_zone("start")
    connect = start.get_connection(start.get_connections())
    zone_connect = connect.get_zone_2()
    print(start.get_drones())
    o.move_drone_between_zones(
        start, zone_connect, connect, start.get_drones()[0]
    )
    print(zone_connect.get_drones())
    print(start.get_drones())


def first_map_try(o: Orchestrator) -> None:
    drones = o.get_drones()
    connections = o.get_connections()
    for i in range(0, len(drones)):
        prev_connect = connections[0].get_zone_1().get_connections()[0]
        for connect in connections:
            result = ""
            if connect.get_zone_1().get_nb_drones() > 0:
                drone_to_move = connect.get_zone_1().get_drones()[0] 
                result = o.move_drone_between_zones(
                    connect.get_zone_1(),
                    connect.get_zone_2(),
                    connect,
                    drone_to_move
                )
            if prev_connect.get_zone_1().get_nb_drones() > 0 and connect.get_zone_1().get_name() != "start":
                drone_to_move = prev_connect.get_zone_1().get_drones()[0]
                result += " "
                result += o.move_drone_between_zones(prev_connect.get_zone_1(),
                                                    prev_connect.get_zone_2(),
                                                    prev_connect,
                                                    drone_to_move
                                                    )
            prev_connect = connect
            if result:
                print(result)


def second_map_try(o: Orchestrator) -> None:
    zones = o.get_zones()
    n_drones = len(o.get_drones())
    goal = zones[len(zones) - 1]
    while goal.get_nb_drones() != n_drones:
        move = ""
        for zone in zones:
            if zone.get_nb_drones() > 0:
                for connection in zone.get_connections():
                    if len(zone.get_connections()) > 1:
                        if connection == zone.get_connections()[0]:
                            continue
                        else:
                            for _, possible in enumerate(zone.get_connections()[1:], start=1):
                                if not possible.get_zone_2().has_max_drones():
                                    if possible.get_zone_1().get_nb_drones() > 0:
                                        drone_to_move = possible.get_zone_1().get_drones()[0]
                                        move += o.move_drone_between_zones(possible.get_zone_1(),
                                                                possible.get_zone_2(),
                                                                possible,
                                                                drone_to_move)
                                        move += " "
                    else:
                        if connection.get_zone_1().get_nb_drones() > 0:
                            drone_to_move = connection.get_zone_1().get_drones()[0]
                            move += o.move_drone_between_zones(connection.get_zone_1(),
                                                               connection.get_zone_2(),
                                                               connection,
                                                               drone_to_move)
        print(move)

def second_map_try_gemini(o: Orchestrator) -> None:
    zones = o.get_zones()
    n_drones = len(o.get_drones())
    goal = zones[-1]

    while goal.get_nb_drones() != n_drones:
        turn_moves = []
        moved_in_this_turn = False


        drones_moved_this_turn = set()


        for zone in reversed(zones):
            if zone == goal or zone.get_nb_drones() == 0:
                continue

            for connection in zone.get_connections():
                current_zone = zone
                next_zone = (
                    connection.get_zone_2()
                    if connection.get_zone_1() == current_zone
                    else connection.get_zone_1()
                )


                if zones.index(next_zone) > zones.index(current_zone):
                    if not next_zone.has_max_drones() and current_zone.get_nb_drones() > 0:


                        drone_to_move = None
                        for drone in current_zone.get_drones():
                            if drone not in drones_moved_this_turn:
                                drone_to_move = drone
                                break

                        if drone_to_move:
                            res = o.move_drone_between_zones(
                                current_zone, next_zone, connection, drone_to_move
                            )

                            if "Couldn't" not in res:
                                turn_moves.append(res)
                                drones_moved_this_turn.add(drone_to_move)
                                moved_in_this_turn = True
                                break

        if turn_moves:
            print(" ".join(turn_moves))

        if not moved_in_this_turn:
            print("Error: Deadlock (no drone could advance)")
            break

def get_reachable_zones(zones: list[Zone], goal: Zone) -> set[Zone]:
    """Return zones from which the goal can be reached."""
    reachable = {goal}
    queue = deque([goal])


    reverse_graph = {zone: [] for zone in zones}
    for zone in zones:
        for conn in zone.get_connections():
            if conn.get_zone_2() == zone:
                reverse_graph[zone].append(conn.get_zone_1())

    while queue:
        current = queue.popleft()
        for parent in reverse_graph.get(current, []):
            if parent not in reachable:
                reachable.add(parent)
                queue.append(parent)

    return reachable


def stoned_try_first(o: Orchestrator) -> None:
    screen, clock, grid = init_display(o)
    show_initial_state(
        o,
        grid,
        screen,
        clock,
        seconds=2,
    )

    zones = o.get_zones()
    goal = zones[-1]
    nb_drones = len(o.get_drones())

    def is_loop_zone(zone: Zone) -> bool:
        return "loop" in zone.get_name().lower()

    def is_dead_end(zone: Zone) -> bool:
        return ("trap" in zone.get_name().lower() or "dead" in zone.get_name().lower())

    valid_zones = get_reachable_zones(zones, goal)

    while goal.get_nb_drones() < nb_drones:
        turn_moves = []
        drones_moved = set()
        for zone in reversed(zones):
            connections = zone.get_connections()

            def connection_priority(conn: Connection):
                target = conn.get_zone_2() if conn.get_zone_1() == zone else conn.get_zone_1()

                if target not in valid_zones:
                    return 3

                if is_loop_zone(zone) and is_loop_zone(target):
                    return 2

                if target.has_restricted():
                    return 1

                return 0

            connections = sorted(connections, key=connection_priority)

            for connection in connections:
                c_zone = zone
                res = ""

                if connection.get_nb_drones() > 0:
                    n_zone = connection.get_zone_2()
                    drone_to_move = connection.get_drones()[0]

                    res += o.move_drone_from_connection_to_hub(
                        n_zone,
                        drone_to_move,
                        connection
                    )
                    res += " "
                    turn_moves.append(res)
                    drones_moved.add(drone_to_move)

                elif connection.get_zone_1() == c_zone:
                    n_zone = connection.get_zone_2()

                    if n_zone not in valid_zones:
                        continue

                    is_priority = n_zone.has_priority()
                    is_restricted = n_zone.has_restricted()

                    while c_zone.get_nb_drones() > 0 and not n_zone.has_max_drones() and c_zone.get_drones()[0] not in drones_moved:
                        if is_priority is True:
                            drone_to_move = c_zone.get_drones()[0]

                            res += o.move_drone_between_zones(
                                c_zone,
                                n_zone,
                                connection,
                                drone_to_move
                            )
                            res += " "
                            turn_moves.append(res)
                            drones_moved.add(drone_to_move)

                        elif not is_priority and not is_restricted and not is_loop_zone(zone):
                            if c_zone.get_nb_drones() > 0:
                                drone_to_move = c_zone.get_drones()[0]

                                res += o.move_drone_between_zones(
                                    c_zone,
                                    n_zone,
                                    connection,
                                    drone_to_move
                                )
                                res += " "
                                turn_moves.append(res)
                                drones_moved.add(drone_to_move)

                        elif is_restricted:
                            drone_to_move = c_zone.get_drones()[0]

                            res += o.move_drone_from_hub_to_connection(
                                c_zone,
                                drone_to_move,
                                connection
                            )
                            turn_moves.append(res)
                            drones_moved.add(drone_to_move)

                        elif is_loop_zone(zone):
                            if c_zone.get_nb_drones() > 0:
                                drone_to_move = c_zone.get_drones()[0]

                                res += o.move_drone_between_zones(
                                    c_zone,
                                    n_zone,
                                    connection,
                                    drone_to_move
                                )
                                res += " "
                                turn_moves.append(res)
                                drones_moved.add(drone_to_move)

                elif connection.get_zone_2() == c_zone:
                    continue

        if turn_moves:
            print(" ".join(turn_moves))

            grid.animate_changes(
                screen,
                clock
            )


def get_dead_ends(zones: list[Zone], start: Zone, goal: Zone) -> set[str]:
    adj = {z.get_name(): set() for z in zones}
    for zone in zones:
        for conn in zone.get_connections():
            z1_name = conn.get_zone_1().get_name()
            z2_name = conn.get_zone_2().get_name()
            if z1_name in adj and z2_name in adj:
                adj[z1_name].add(z2_name)
                adj[z2_name].add(z1_name)

    active_zone_names = {z.get_name() for z in zones}
    changed = True

    while changed:
        changed = False
        to_remove = []
        for z_name in active_zone_names:
            if z_name == start.get_name() or z_name == goal.get_name():
                continue
            active_neighbors = adj[z_name].intersection(active_zone_names)
            if len(active_neighbors) <= 1:
                to_remove.append(z_name)

        if to_remove:
            for z_name in to_remove:
                active_zone_names.remove(z_name)
            changed = True

    return {z.get_name() for z in zones} - active_zone_names


def compute_distances_to_goal(
    zones: list[Zone], goal: Zone
) -> dict[str, int]:
    goal_name = goal.get_name()
    distances = {goal_name: 0}
    queue = [goal]

    while queue:
        current = queue.pop(0)
        current_name = current.get_name()
        current_dist = distances[current_name]

        for zone in zones:
            for conn in zone.get_connections():
                z1 = conn.get_zone_1()
                z2 = conn.get_zone_2()
                neighbor = z1 if z2 == current else (z2 if z1 == current else None)

                if neighbor:
                    neighbor_name = neighbor.get_name()
                    if neighbor_name not in distances:
                        distances[neighbor_name] = current_dist + 1
                        queue.append(neighbor)

    return distances


def calculate_dijkstra_weights(c_zone, n_zone, dead_end_names, distances_map, weights, is_high_stress=False):
    n_name = n_zone.get_name()
    c_name = c_zone.get_name()

    if n_zone.has_blocked() or n_name in dead_end_names or n_name not in distances_map:
        return float('inf')

    d_current = distances_map.get(c_name, float('inf'))
    d_target = distances_map.get(n_name, float('inf'))

    cost = 1.0
    if d_target >= d_current:
        cost += weights["w_loop"]
    else:
        if n_zone.has_priority():
            cost -= weights["w_priority"]

    if n_zone.has_restricted():
        cost += weights["w_restricted"]

    has_restricted_neighbor = any(
        (conn.get_zone_1() == n_zone and conn.get_zone_2().has_restricted()) or
        (conn.get_zone_2() == n_zone and conn.get_zone_1().has_restricted())
        for conn in n_zone.get_connections()
    )
    if has_restricted_neighbor and not n_zone.has_restricted():
        cost += weights.get("w_trap_proximity", 500.0)

    if is_high_stress:
        current_drones = n_zone.get_nb_drones()
        if n_zone.has_max_drones():
            if current_drones > 0:
                cost += weights.get("w_congestion", 200.0) * current_drones
        else:
            cost += current_drones * 10.0

    return cost


def run_turn_execution(o, weights, dead_end_names, distances_map, is_high_stress=False, is_simulation=True, screen=None, clock=None, grid=None):
    zones = o.get_zones()
    goal = zones[-1]
    nb_drones = len(o.get_drones())

    all_connections = []
    seen_conns = set()
    for z in zones:
        for conn in z.get_connections():
            if id(conn) not in seen_conns:
                seen_conns.add(id(conn))
                all_connections.append(conn)


    drone_connection_target = {}
    total_turns = 0

    while goal.get_nb_drones() < nb_drones:
        turn_moves = []
        drones_moved = set()
        total_turns += 1


        for connection in all_connections:
            initial_conn = connection.get_nb_drones()
            processed_conn = 0

            while connection.get_nb_drones() > 0 and processed_conn < initial_conn:
                drone_to_move = connection.get_drones()[0]
                if drone_to_move in drones_moved:
                    break


                target_zone = drone_connection_target.get(drone_to_move)
                if not target_zone:
                    z1 = connection.get_zone_1()
                    z2 = connection.get_zone_2()
                    d1 = distances_map.get(z1.get_name(), float('inf'))
                    d2 = distances_map.get(z2.get_name(), float('inf'))
                    target_zone = z2 if d2 < d1 else z1

                if target_zone.has_max_drones():
                    break

                res = o.move_drone_from_connection_to_hub(target_zone, drone_to_move, connection)
                if res != "Error" and not res.startswith("Couldn't"):
                    turn_moves.append(res + " ")
                    drones_moved.add(drone_to_move)
                    drone_connection_target.pop(drone_to_move, None)
                else:
                    break
                processed_conn += 1


        for zone in reversed(zones):
            connections = zone.get_connections()

            def get_cost(conn):
                n_zone = conn.get_zone_2() if conn.get_zone_1() == zone else conn.get_zone_1()
                return calculate_dijkstra_weights(zone, n_zone, dead_end_names, distances_map, weights, is_high_stress)

            connections = sorted(connections, key=get_cost)

            for connection in connections:
                c_zone = zone

                if connection.get_zone_1() == c_zone:
                    n_zone = connection.get_zone_2()
                elif connection.get_zone_2() == c_zone:
                    n_zone = connection.get_zone_1()
                else:
                    continue

                n_name = n_zone.get_name()

                if n_name in dead_end_names or n_name not in distances_map:
                    continue

                d_current = distances_map.get(c_zone.get_name(), float('inf'))
                d_target = distances_map.get(n_name, float('inf'))

                if d_target >= d_current:
                    continue

                initial_hub = c_zone.get_nb_drones()
                processed_hub = 0

                while (
                    c_zone.get_nb_drones() > 0 
                    and not n_zone.has_max_drones() 
                    and processed_hub < initial_hub
                ):
                    drone_to_move = c_zone.get_drones()[0]
                    if drone_to_move in drones_moved:
                        break

                    if n_zone.has_restricted():
                        res = o.move_drone_from_hub_to_connection(c_zone, drone_to_move, connection)
                    else:
                        res = o.move_drone_between_zones(c_zone, n_zone, connection, drone_to_move)

                    if res != "Error" and not res.startswith("Couldn't"):
                        turn_moves.append(res + " ")
                        drones_moved.add(drone_to_move)

                        drone_connection_target[drone_to_move] = n_zone
                    else:
                        break
                    processed_hub += 1

        if turn_moves and not is_simulation:
            print("".join(turn_moves).strip())
            if grid and screen and clock:
                grid.animate_changes(screen, clock)

        if total_turns > 300:
            return float('inf')

    return total_turns


def stoned_try(o: Orchestrator) -> None:
    zones = o.get_zones()
    start = zones[0]
    goal = zones[-1]

    dead_end_names = get_dead_ends(zones, start, goal)
    distances_map = compute_distances_to_goal(zones, goal)

    nb_drones = len(o.get_drones())
    is_high_stress = (nb_drones >= 20)

    weight_candidates = [
        {"w_loop": 50.0, "w_restricted": 50.0, "w_priority": 2.0, "w_trap_proximity": 500.0, "w_congestion": 200.0},
        {"w_loop": 100.0, "w_restricted": 100.0, "w_priority": 5.0, "w_trap_proximity": 1000.0, "w_congestion": 400.0},
        {"w_loop": 30.0, "w_restricted": 30.0, "w_priority": 3.0, "w_trap_proximity": 300.0, "w_congestion": 100.0},
    ]

    best_turns = float("inf")
    best_weights = weight_candidates[0]
    consecutive_same_counter = 0

    for weights in weight_candidates:
        try:
            sim_orchestrator = copy.deepcopy(o)
        except Exception:
            break

        turns = run_turn_execution(sim_orchestrator, weights, dead_end_names, distances_map, is_high_stress=is_high_stress, is_simulation=True)

        if turns == best_turns:
            consecutive_same_counter += 1
        elif turns < best_turns:
            best_turns = turns
            best_weights = weights
            consecutive_same_counter = 1
        else:
            consecutive_same_counter = 0

        if consecutive_same_counter == 8:
            break

    if best_turns == float("inf"):
        print("The map cannot be solved.")
        return

    screen, clock, grid = init_display(o)
    show_initial_state(o, grid, screen, clock, seconds=2)
    print(f"\n--- Solution has: {best_turns} turns ---")
    run_turn_execution(
        o, 
        best_weights, 
        dead_end_names, 
        distances_map, 
        is_high_stress=is_high_stress,
        is_simulation=False, 
        screen=screen, 
        clock=clock, 
        grid=grid
    )

from drone import Drone
from zone import Zone
from connection import Connection
from orchestrator import Orchestrator
import sys
from collections import deque

def basic_test(o: Orchestrator) -> None:
    zones = o.get_zones()
    drones = o.get_drones()
    connections = o.get_connections()
    start = o.get_zone("start")
    goal = o.get_zone("goal")
    connect = start.get_connection(start.get_connections())
    zone_connect = connect.get_zone_2()
    print(start.get_drones())
    o.move_drone_between_zones(start,
                               zone_connect,
                               connect,
                               start.get_drones())
    print(zone_connect.get_drones())
    print(start.get_drones())


def first_map_try(o: Orchestrator) -> None:
    zones = o.get_zones()
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
    while goal.get_nb_drones() != n_drones: # mientras que todos los drones no esten en la meta
        move = ""
        for zone in zones: # miramos todas las zonas
            if zone.get_nb_drones() > 0: # si hay por lo menos un dron
                for connection in zone.get_connections(): #miramos todas las conexiones posibles
                    if len(zone.get_connections()) > 1: # si hay mas de una conexion
                        if connection == zone.get_connections()[0]: # si la conexion es la primera posible de la lista
                            continue # no hacemos nada porque es una hacia atras
                        else: # hay varias pero no usamos la que va hacia atras
                            for _, possible in enumerate(zone.get_connections()[1:], start=1): # miro todas las conexiones posibles
                                if not possible.get_zone_2().has_max_drones(): # si no tiene el maximo numero de drones
                                    if possible.get_zone_1().get_nb_drones() > 0: # si hay drones en la zona
                                        drone_to_move = possible.get_zone_1().get_drones()[0] #preparamos el dron a mover
                                        move += o.move_drone_between_zones(possible.get_zone_1(),
                                                                possible.get_zone_2(),
                                                                possible,
                                                                drone_to_move) # lo movemos
                                        move += " "
                    else: # solo hay una conexion
                        if connection.get_zone_1().get_nb_drones() > 0: #si hay drones
                            drone_to_move = connection.get_zone_1().get_drones()[0] # preparamos el dron
                            move += o.move_drone_between_zones(connection.get_zone_1(),
                                                               connection.get_zone_2(),
                                                               connection,
                                                               drone_to_move) # lo movemos
        print(move)

def second_map_try_gemini(o: Orchestrator) -> None:
    zones = o.get_zones()
    n_drones = len(o.get_drones())
    goal = zones[-1]

    while goal.get_nb_drones() != n_drones:
        turn_moves = []
        moved_in_this_turn = False
        
        # CONTROL: Ningún dron puede moverse más de 1 vez por turno
        drones_moved_this_turn = set()

        # RECORRIDO INVERSO: De la meta hacia el inicio para liberar espacio y evitar doble salto
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

                # Comprobar que avanzamos hacia la meta (índice mayor en zonas)
                if zones.index(next_zone) > zones.index(current_zone):
                    if not next_zone.has_max_drones() and current_zone.get_nb_drones() > 0:
                        
                        # Buscar un dron en la zona que AÚN NO se haya movido este turno
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
                                drones_moved_this_turn.add(drone_to_move) # Bloqueamos el dron este turno
                                moved_in_this_turn = True
                                break  # Pasamos a la siguiente zona para dar turno a otros drones

        if turn_moves:
            print(" ".join(turn_moves))

        if not moved_in_this_turn:
            print("Error: Deadlock (ningún dron pudo avanzar)")
            break

def get_reachable_zones(zones, goal) -> set:
    """Calcula todas las zonas desde las que realmente se puede llegar a 'goal'."""
    reachable = {goal}
    queue = deque([goal])
    
    # Construir grafo inverso (zone_2 -> zone_1)
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


def stoned_try(o: Orchestrator) -> None:
    zones = o.get_zones()
    goal = zones[-1]
    nb_drones = len(o.get_drones())
    def is_loop_zone(zone: Zone) -> bool:
        return "loop" in zone.get_name().lower()
    def is_dead_end(zone: Zone) -> bool:
        return ("trap" in zone.get_name().lower() or "dead" in zone.get_name().lower())
    valid_zones = get_reachable_zones(zones, goal)

    while goal.get_nb_drones() < nb_drones:  # cada turno que todos los drones no esten en la meta
        turn_moves = []
        for zone in reversed(zones):
            has_a_drone_moved = False
            drones_moved = set()
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

                if connection.get_nb_drones() > 0: #si hay algun dron en una conexion (porque nos hemos movido en un restringido
                    n_zone = connection.get_zone_2()
                    drone_to_move = connection.get_drones()[0]
                    res += o.move_drone_from_connection_to_hub(n_zone,
                                                            drone_to_move,
                                                            connection)
                    res += " "
                    turn_moves.append(res)
                    has_a_drone_moved = True
                    drones_moved.add(drone_to_move)
                elif connection.get_zone_1() == c_zone: # si estamos avanzando hacia delante
                    n_zone = connection.get_zone_2()
                    if n_zone not in valid_zones:
                        continue
                    is_priority = n_zone.has_priority()
                    is_restricted = n_zone.has_restricted()

                    if c_zone.get_nb_drones() > 0 and not n_zone.has_max_drones(): #si hay drones que mover en la zona y la zona no esta llena
                        if is_priority is True:
                            drone_to_move = c_zone.get_drones()[0]
                            res += o.move_drone_between_zones(c_zone,
                                                            n_zone,
                                                            connection,
                                                            drone_to_move)
                            res += " "
                            turn_moves.append(res)
                            has_a_drone_moved = True
                            drones_moved.add(drone_to_move)
                        elif not is_priority and not is_restricted:
                            if c_zone.get_nb_drones() > 0:
                                drone_to_move = c_zone.get_drones()[0]
                                res += o.move_drone_between_zones(c_zone,
                                                                n_zone,
                                                                connection,
                                                                drone_to_move)
                                res += " "
                                turn_moves.append(res)
                                has_a_drone_moved = True
                                drones_moved.add(drone_to_move)
                        elif is_restricted and not has_a_drone_moved: # me muevo en el restringido unicamente si no ha podido moverse ningun dron aun
                            drone_to_move = c_zone.get_drones()[0]
                            res += o.move_drone_from_hub_to_connection(c_zone,
                                                                    drone_to_move,
                                                                    connection)
                            turn_moves.append(res)
                            drones_moved.add(drone_to_move)
                            has_a_drone_moved = True
                elif connection.get_zone_2() == c_zone:
                    continue #aquí la idea es pasar a la siguiente conexión
        if turn_moves:
            print(" ".join(turn_moves))
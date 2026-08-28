from drone import Drone
from zone import Zone
from connection import Connection
from orchestrator import Orchestrator


def basic_test(o: Orchestrator) -> None:
    zones = o.get_zones()
    drones = o.get_drones()
    connections = o.get_connections()
    start = o.get_zone("start")
    goal = o.get_zone("goal")
    connect = start.get_connection(start.get_connections())
    print(connect.show_info())
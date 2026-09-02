from orchestrator import Orchestrator


def basic_test(o: Orchestrator) -> None:
    start = o.get_zone("start")
    connect = start.get_connection(start.get_connections())
    print(connect.show_info())
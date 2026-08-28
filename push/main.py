from parsing import parse_map
from parsing import MapData, HubData, ConnectionData
from drone import DroneFactory, Drone
from zone import ZoneFactory, Zone
from connection import ConnectionFactory, Connection
from typing import cast
from orchestrator import Orchestrator
from algorithms import basic_test
import sys


def initialize(map_data: MapData) -> Orchestrator:
    h_factory = ZoneFactory()
    h_list: list[Zone] = []
    c_factory = ConnectionFactory()
    c_list: list[Connection] = []

    def find_zone(name: str) -> Zone:
        for zone in h_list:
            if zone.name == name:
                return zone
        sys.exit(1)

    for i in map_data:
        if i["type"] == "nb_drones" and isinstance(i["data"], str):
            d_factory = DroneFactory()
            drone_list: list[Drone] = []
            drone_index = 0
            for j in range(0, int(i["data"])):
                drone_list.append(d_factory.create_drone(drone_index))
                drone_index += 1
        if (i["type"] == "hub"
           or i["type"] == "start_hub" or
           i["type"] == "end_hub"):
            data = i["data"]
            if isinstance(data, dict) and "name" in data:
                data = cast(HubData, data)
                h_name = data["name"]
                h_coords = data["coordinates"]
                h_options = data["options"]
                max_drones = 9999
                if i["type"] == "hub":
                    if ("max_drones" in h_options):
                        max_drones = int(h_options["max_drones"])
                    else:
                        max_drones = 1
                h_list.append(h_factory.create_zone(h_name,
                                                    [],
                                                    h_coords,
                                                    h_options,
                                                    max_drones))
        if (i["type"] == "connection"):
            data = i["data"]
            if isinstance(data, dict) and "from_" in data:
                data = cast(ConnectionData, data)
                zone1 = find_zone(data["from_"])
                zone2 = find_zone(data["to"])
                max_cap = 1
                if "options" in data:
                    d_options = data["options"]
                    max_capacity = d_options.get("max_link_capacity")
                    max_cap = int(max_capacity) if (max_capacity
                                                    is not None) else 1
                c_list.append(c_factory.create_connection(zone1,
                                                          zone2,
                                                          max_cap))
    for k in h_list:
        for c in c_list:
            k.add_connection(c)
        if k.get_name() == "start":
            for drone in drone_list:
                k.add_drone(drone)

    orchestrator = Orchestrator(drone_list,
                                h_list,
                                c_list)
    return orchestrator


def main() -> None:
    map_data = parse_map("maps/easy/01_linear_path.txt")
    simulation = initialize(map_data)
    basic_test(simulation)


if __name__ == "__main__":
    main()

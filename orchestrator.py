from drone import Drone
from zone import Zone
from connection import Connection
import sys


class Orchestrator:
    def __init__(self,
                 drones: list[Drone],
                 zones: list[Zone],
                 connections: list[Connection]) -> None:
        self.drones = drones
        self.zones = zones
        self.connections = connections

    def show_info(self) -> str:
        return (f"Drones: {self.drones}"
                f" Zones: {self.zones}"
                f" Connections: {self.connections}")

    def get_zones(self) -> list[Zone]:
        return self.zones

    def get_drones(self) -> list[Drone]:
        return self.drones

    def get_connections(self) -> list[Connection]:
        return self.connections

    def get_zone(self, name) -> Zone:
        for i in self.zones:
            if i.get_name() == name:
                return i
        print("Error in get_zone")
        sys.exit(1)

    def get_connected_zone(self, hub: Zone, connection: Connection) -> Zone:
        if connection.get_zone_1() == hub:
            return connection.get_zone_2()
        print("Error in get_connected_zone")
        sys.exit(1)

    @staticmethod
    def get_drone_from_zone(zone: Zone, index: int) -> Drone:
        drones = zone.get_drones()
        for i in drones:
            if i.get_index() == index:
                return i
        sys.exit(1)

    def move_drone_from_hub_to_connection(
        self, hub: Zone, drone: Drone, connection: Connection
    ) -> str:
        if (
            drone in hub.get_drones()
            and connection.get_max_link_cap() > connection.get_nb_drones()
        ):
            hub.remove_drone(drone)
            connection.add_drone(drone)
            return f"D{drone.get_index()}-C{connection.get_name()}"
        return "Error"

    def move_drone_from_connection_to_hub(
        self, hub: Zone, drone: Drone, connection: Connection
    ) -> str:
        if (
            drone in connection.get_drones()
            and hub.get_max_nb_drones() > hub.get_nb_drones()
        ):
            connection.remove_drone(drone) 
            hub.add_drone(drone)
            return f"D{drone.get_index()}-C{connection.get_name()}"
        return "Error"

    def move_drone_between_zones(
        self,
        hub1: Zone,
        hub2: Zone,
        connection: Connection,
        drone: Drone,
    ) -> str:
        if self.move_drone_from_hub_to_connection(hub1, drone, connection) not in "Error":
            if self.move_drone_from_connection_to_hub(hub2, drone, connection) not in "Error":
                return f"D{drone.get_index()}-{hub2.get_name()}"
            else:
                pass

        return f"Couldn't move the drone between zones {hub1.get_name()} and {hub2.get_name()}"
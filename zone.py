from __future__ import annotations
from drone import Drone
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from connection import Connection
import sys


class Zone:
    has_max_nb_drones: bool = False
    connections: list[Connection] = []

    def __init__(self,
                 name: str,
                 drones: list[Drone],
                 coordinates: tuple[int, int],
                 special_options: dict[str, str],
                 max_nb_drones: int = 1,):
        self.name = name
        self.drones = drones
        self.max_nb_drones = max_nb_drones
        self.coordinates = coordinates
        self.special_options = special_options
        self.is_priority = False
        self.is_restricted = False
        if "priority" in special_options.values():
            self.is_priority = True
        elif "restricted" in special_options.values():
            self.is_restricted = True

    def add_connection(self, connection: Connection) -> None:
        if (connection.get_zone_1().get_name() == self.get_name()
           or connection.get_zone_2().get_name() == self.get_name()):
            if connection not in self.connections:
                self.connections.append(connection)

    def has_priority(self) -> bool:
        return self.is_priority

    def has_restricted(self) -> bool:
        return self.is_restricted


    def get_nb_drones(self) -> int:
        return len(self.drones)

    def get_max_nb_drones(self) -> int:
        return self.max_nb_drones

    def get_name(self) -> str:
        return self.name

    def get_connections(self) -> list[Connection]:
        return self.connections

    def get_connection(self, connections: Connection) -> Connection:
        for i in self.connections:
            if i == connections:
                return i
        print("Error in get_connection")
        sys.exit(1)

    def get_connection_names(self) -> list[str]:
        connections_info: list[str] = []
        for i in self.connections:
            connections_info.append(i.show_info())
        return connections_info

    def show_info(self) -> str:
        return (f"Zone {self.name} in coordinates {self.coordinates} has"
                f" {len(self.drones)} drones and"
                f" a maximum of {self.max_nb_drones} drones."
                f" its special options are {self.special_options}"
                f" Its connections are {self.get_connection_names()}")

    def add_drone(self, drone: Drone) -> None:
        if self.has_max_nb_drones is False:
            self.drones.append(drone)
        if len(self.drones) >= self.max_nb_drones:
            self.has_max_nb_drones = True

    def remove_drone(self, drone: Drone) -> None:
        self.drones.remove(drone)
        if len(self.drones) < self.max_nb_drones:
            self.has_max_nb_drones = False

    def get_drones(self) -> list[Drone]:
        return self.drones

    def has_max_drones(self) -> bool:
        if self.get_nb_drones() == self.get_max_nb_drones():
            return True
        return False


class ZoneFactory:
    def create_zone(self,
                    name: str,
                    drones: list[Drone],
                    coordinates: tuple[int, int],
                    special_options: dict[str, str],
                    max_nb_drones: int) -> Zone:
        return Zone(name,
                    drones,
                    coordinates,
                    special_options,
                    max_nb_drones)

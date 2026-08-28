from __future__ import annotations
from typing import TYPE_CHECKING
from drone import Drone
if TYPE_CHECKING:
    from zone import Zone


class Connection:
    has_max_link_cap: bool = False
    def __init__(self,
                 zone1: Zone,
                 zone2: Zone,
                 max_link_cap: int,
                 drones: list[Drone],
                 ) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_cap = max_link_cap
        self.drones = drones

    def get_name(self) -> str:
        return f"{self.get_zone_1().get_name()}-{self.get_zone_2().get_name()}"

    def get_nb_drones(self) -> int:
        return len(self.drones)

    def get_drones(self) -> list[Drone]:
        return self.drones

    def get_zone_1(self) -> Zone:
        return self.zone1

    def get_zone_2(self) -> Zone:
        return self.zone2

    def get_max_link_cap(self) -> int:
        return self.max_link_cap

    def show_info(self) -> str:
        return (f"This connection is between {self.zone1.get_name()} and"
                f" {self.zone2.get_name()}"
                f" It has {str(self.get_nb_drones())} drones traveling and"
                f" it's maximum drone cap is {self.max_link_cap}")

    def add_drone(self, drone: Drone) -> None:
        if not self.has_max_link_cap:
            self.drones.append(drone)
        if len(self.drones) >= self.max_link_cap:
            self.has_max_link_cap = True

    def remove_drone(self, drone: Drone) -> None:
        self.drones.remove(drone)
        if len(self.drones) < self.max_link_cap:
            self.has_max_link_cap = False


class ConnectionFactory:
    def create_connection(self,
                          zone1: Zone,
                          zone2: Zone,
                          max_link_cap: int,) -> Connection:
        return Connection(zone1,
                          zone2,
                          max_link_cap,
                          [])

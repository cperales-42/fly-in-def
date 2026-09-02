class Drone:
    def __init__(self, location: str, index: int) -> None:
        self.location = location
        self.index = index

    def show_info(self) -> str:
        return f"Drone n{self.index} is at {self.location}"

    def get_location(self) -> str:
        return self.location

    def update_location(self, new_location: str) -> str:
        self.location = new_location
        return self.location

    def get_index(self) -> int:
        return self.index


class DroneFactory:
    def create_drone(self, index: int) -> Drone:
        return Drone("start_hub", index)

from typing import TypeAlias, TypedDict
import sys


Coordinate: TypeAlias = tuple[int, int]
Options: TypeAlias = dict[str, str]


class HubData(TypedDict, total=False):
    name: str
    coordinates: Coordinate
    options: Options


class ConnectionData(TypedDict, total=False):
    from_: str
    to: str
    options: Options


class MapElement(TypedDict):
    type: str
    data: HubData | ConnectionData | str


MapData: TypeAlias = list[MapElement]


def is_number(nb: str) -> bool:
    try:
        float(nb)
        return True
    except ValueError:
        return False


def add_optional_dict(value: list[str]) -> Options:
    optional_dict: Options = {}
    for item in value:
        item = item.strip("[]")
        if "=" in item:
            key, dict_value = item.split("=", 1)
            optional_dict[key] = dict_value
    return optional_dict


def parse_map(map_path: str) -> MapData:
    try:
        map_data: MapData = []
        with open(map_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    raise SyntaxError(
                        "Invalid line format: missing ':'"
                    )
                values: list[str] = line.split()
                kind: str = values[0]
                if kind == "nb_drones:":
                    if len(values) < 2:
                        raise SyntaxError(
                            "Invalid nb_drones format"
                        )
                    data: MapElement = {
                        "type": "nb_drones",
                        "data": values[1],
                    }
                elif kind in ("start_hub:", "hub:", "end_hub:"):
                    if len(values) < 4:
                        raise SyntaxError(
                            f"Invalid {kind} format"
                        )
                    coordinates: Coordinate = (
                        int(values[2]),
                        int(values[3]),
                    )
                    hub: HubData = {
                        "name": values[1],
                        "coordinates": coordinates,
                    }
                    optional: Options = add_optional_dict(
                        values[4:]
                    )
                    if optional:
                        hub["options"] = optional
                    data = {
                        "type": kind[:-1],
                        "data": hub,
                    }
                elif kind == "connection:":
                    if len(values) < 2:
                        raise SyntaxError(
                            "Invalid connection format"
                        )
                    start, end = values[1].split("-", 1)
                    connection: ConnectionData = {
                        "from_": start,
                        "to": end,
                    }
                    optional = add_optional_dict(values[2:])

                    if optional:
                        connection["options"] = optional
                    data = {
                        "type": "connection",
                        "data": connection,
                    }
                else:
                    raise SyntaxError(
                        f"Unknown map element: {kind}"
                    )
                map_data.append(data)
        return map_data
    except (OSError, ValueError, SyntaxError) as e:
        print(f"Caught exception: {e}")
        sys.exit(1)

import re
import sys
from typing import TypeAlias, TypedDict


Coordinate: TypeAlias = tuple[int, int]
Options: TypeAlias = dict[str, str]
ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
ZONE_KEYS = {"zone", "color", "max_drones"}
CONNECTION_KEYS = {"max_link_capacity"}


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


def _error(line_number: int, cause: str) -> SyntaxError:
    return SyntaxError(f"line {line_number}: {cause}")


def _parse_options(
    metadata: str | None,
    allowed_keys: set[str],
    line_number: int,
) -> Options:
    if metadata is None:
        return {}
    if not metadata:
        raise _error(line_number, "metadata block cannot be empty")

    options: Options = {}
    for item in metadata.split():
        if "=" not in item:
            raise _error(line_number, f"invalid metadata item '{item}'")
        key, value = item.split("=", 1)
        if not key or not value:
            raise _error(line_number, f"invalid metadata item '{item}'")
        if key not in allowed_keys:
            raise _error(line_number, f"unknown metadata key '{key}'")
        if key in options:
            raise _error(line_number, f"duplicate metadata key '{key}'")
        if key == "color":
            _validate_color(value, line_number)
        options[key] = value
    return options


def _positive_capacity(value: str, name: str, line_number: int) -> None:
    if re.fullmatch(r"[0-9]+", value) is None or int(value) <= 0:
        raise _error(line_number, f"{name} must be a positive integer")


def _validate_color(value: str, line_number: int) -> None:
    if value.lower() == "rainbow":
        return

    import pygame

    try:
        pygame.Color(value)
    except ValueError as error:
        raise _error(line_number, f"invalid pygame color '{value}'") from error


def parse_map(map_path: str) -> MapData:
    map_data: MapData = []
    zone_names: set[str] = set()
    connection_names: set[frozenset[str]] = set()
    connection_counts: dict[str, int] = {}
    start_count = 0
    end_count = 0
    first_significant_line = True
    last_line_number = 1
    zone_records: list[tuple[int, str, HubData]] = []

    try:
        with open(map_path, "r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                last_line_number = line_number
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                if first_significant_line:
                    first_significant_line = False
                    drone_match = re.fullmatch(r"nb_drones:\s+(\S+)", line)
                    if drone_match is None:
                        raise _error(
                            line_number,
                            "first significant line must be 'nb_drones: "
                            "<positive_integer>'",
                        )
                    drone_count = drone_match.group(1)
                    _positive_capacity(drone_count, "nb_drones", line_number)
                    map_data.append({"type": "nb_drones", "data": drone_count})
                    continue

                zone_match = re.fullmatch(
                    r"(start_hub|hub|end_hub):\s+([^\s-]+)\s+"
                    r"(-?\d+)\s+(-?\d+)(?:\s+\[(.*)\])?",
                    line,
                )
                if zone_match is not None:
                    zone_type, name, x_value, y_value, metadata = zone_match.groups()
                    if name in zone_names:
                        raise _error(line_number, f"duplicate zone name '{name}'")
                    options = _parse_options(metadata, ZONE_KEYS, line_number)
                    if "zone" in options and options["zone"] not in ZONE_TYPES:
                        raise _error(
                            line_number,
                            f"invalid zone type '{options['zone']}'",
                        )
                    if zone_type == "hub" and "max_drones" in options:
                        _positive_capacity(
                            options["max_drones"], "max_drones", line_number
                        )
                    if zone_type == "start_hub":
                        start_count += 1
                    elif zone_type == "end_hub":
                        end_count += 1
                    zone_names.add(name)
                    hub: HubData = {
                        "name": name,
                        "coordinates": (int(x_value), int(y_value)),
                    }
                    if options:
                        hub["options"] = options
                    zone_records.append((line_number, zone_type, hub))
                    map_data.append({"type": zone_type, "data": hub})
                    continue

                connection_match = re.fullmatch(
                    r"connection:\s+([^\s-]+)-([^\s-]+)"
                    r"(?:\s+\[(.*)\])?",
                    line,
                )
                if connection_match is not None:
                    first_zone, second_zone, metadata = connection_match.groups()
                    if first_zone not in zone_names or second_zone not in zone_names:
                        raise _error(
                            line_number,
                            "connections must reference previously defined zones",
                        )
                    if first_zone == second_zone:
                        raise _error(line_number, "a connection cannot link a zone to itself")
                    connection_name = frozenset((first_zone, second_zone))
                    if connection_name in connection_names:
                        raise _error(line_number, "duplicate connection")
                    options = _parse_options(
                        metadata, CONNECTION_KEYS, line_number
                    )
                    if "max_link_capacity" in options:
                        _positive_capacity(
                            options["max_link_capacity"],
                            "max_link_capacity",
                            line_number,
                        )
                    connection_counts[first_zone] = (
                        connection_counts.get(first_zone, 0) + 1
                    )
                    connection_counts[second_zone] = (
                        connection_counts.get(second_zone, 0) + 1
                    )
                    connection_names.add(connection_name)
                    connection: ConnectionData = {
                        "from_": first_zone,
                        "to": second_zone,
                    }
                    if options:
                        connection["options"] = options
                    map_data.append({"type": "connection", "data": connection})
                    continue

                raise _error(line_number, "invalid syntax")

        if first_significant_line:
            raise _error(1, "map is empty")
        if start_count != 1:
            raise _error(
                last_line_number,
                f"map must contain exactly one start_hub, found {start_count}",
            )
        if end_count != 1:
            raise _error(
                last_line_number,
                f"map must contain exactly one end_hub, found {end_count}",
            )
        start_record = next(
            record for record in zone_records if record[1] == "start_hub"
        )
        end_record = next(
            record for record in zone_records if record[1] == "end_hub"
        )
        _, start_y = start_record[2]["coordinates"]
        end_x, _ = end_record[2]["coordinates"]
        end_record[2]["coordinates"] = (end_x, start_y)

        original_coordinates = [
            hub["coordinates"] for _, _, hub in zone_records
        ]
        resolved_coordinates: list[Coordinate] = []
        for index, (_, _, hub) in enumerate(zone_records):
            x_value, y_value = hub["coordinates"]
            future_coordinates = set(original_coordinates[index + 1:])
            while (
                (x_value, y_value) in future_coordinates
                or (x_value, y_value) in resolved_coordinates
            ):
                x_value -= 1
                if connection_counts.get(hub["name"], 0) > 1:
                    y_value -= 1
            hub["coordinates"] = (x_value, y_value)
            resolved_coordinates.append((x_value, y_value))

        coordinate_limit = len(zone_names) * 2
        for line_number, _, hub in zone_records:
            x_value, y_value = hub["coordinates"]
            if abs(x_value) > coordinate_limit or abs(y_value) > coordinate_limit:
                raise _error(
                    line_number,
                    "coordinates must be between "
                    f"-{coordinate_limit} and {coordinate_limit}",
                )
        return map_data
    except (OSError, SyntaxError) as error:
        print(f"Map parsing error: {error}")
        sys.exit(1)

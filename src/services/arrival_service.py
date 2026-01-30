"""Train arrival service."""
import logging
from dataclasses import dataclass
from typing import Literal, Optional

from ..data.types import Station, TrainArrival

logger = logging.getLogger(__name__)
from ..data.stations import find_station_by_name
from ..data.lines import is_express_line
from ..gtfs.client import get_arrivals_at_stop, get_arrivals_at_stop_multi_line
from ..utils.time import get_minutes_away
from .direction_parser import parse_direction, get_direction_label


class StationNotFoundError(Exception):
    """Raised when a station cannot be found."""
    def __init__(self, query: str):
        super().__init__(f'Station not found: "{query}"')
        self.query = query


@dataclass
class ArrivalQuery:
    station: str
    line: Optional[str] = None
    direction: Optional[str] = None
    limit: int = 5


@dataclass
class ArrivalResult:
    station: Station
    arrivals: list[TrainArrival]
    query: ArrivalQuery


# Terminal station names by line and direction
TERMINALS: dict[str, dict[str, str]] = {
    "1": {"N": "Van Cortlandt Park-242 St", "S": "South Ferry"},
    "2": {"N": "Wakefield-241 St", "S": "Flatbush Av-Brooklyn College"},
    "3": {"N": "Harlem-148 St", "S": "New Lots Av"},
    "4": {"N": "Woodlawn", "S": "Crown Heights-Utica Av"},
    "5": {"N": "Eastchester-Dyre Av", "S": "Flatbush Av-Brooklyn College"},
    "6": {"N": "Pelham Bay Park", "S": "Brooklyn Bridge-City Hall"},
    "7": {"N": "Flushing-Main St", "S": "34 St-Hudson Yards"},
    "A": {"N": "Inwood-207 St", "S": "Far Rockaway-Mott Av"},
    "C": {"N": "168 St", "S": "Euclid Av"},
    "E": {"N": "Jamaica Center-Parsons/Archer", "S": "World Trade Center"},
    "B": {"N": "Bedford Park Blvd", "S": "Brighton Beach"},
    "D": {"N": "Norwood-205 St", "S": "Coney Island-Stillwell Av"},
    "F": {"N": "Jamaica-179 St", "S": "Coney Island-Stillwell Av"},
    "M": {"N": "Forest Hills-71 Av", "S": "Middle Village-Metropolitan Av"},
    "G": {"N": "Court Sq", "S": "Church Av"},
    "J": {"N": "Jamaica Center-Parsons/Archer", "S": "Broad St"},
    "Z": {"N": "Jamaica Center-Parsons/Archer", "S": "Broad St"},
    "L": {"N": "8 Av", "S": "Canarsie-Rockaway Pkwy"},
    "N": {"N": "Astoria-Ditmars Blvd", "S": "Coney Island-Stillwell Av"},
    "Q": {"N": "96 St", "S": "Coney Island-Stillwell Av"},
    "R": {"N": "Forest Hills-71 Av", "S": "Bay Ridge-95 St"},
    "W": {"N": "Astoria-Ditmars Blvd", "S": "Whitehall St-South Ferry"},
    "S": {"N": "Grand Central-42 St", "S": "Times Sq-42 St"},
}


def _get_terminal_name(line: str, direction: Literal["N", "S"]) -> str:
    """Get terminal station name for a line and direction."""
    terminal = TERMINALS.get(line.upper())
    if not terminal:
        return "Uptown" if direction == "N" else "Downtown"
    return terminal[direction]


def _is_terminal_station(station: Station, line: Optional[str] = None) -> bool:
    """Check if a station is a terminal (end of line) for any of its lines.

    At terminal stations, trains arrive with one direction but depart with the opposite.
    For example, at South Ferry (southern terminal of the 1), trains arrive as 'S' but depart as 'N'.
    """
    lines_to_check = [line.upper()] if line else station.lines
    station_name_lower = station.name.lower()

    for check_line in lines_to_check:
        terminals = TERMINALS.get(check_line.upper())
        if terminals:
            # Check if station name matches either terminal
            for terminal_name in terminals.values():
                if terminal_name.lower() in station_name_lower or station_name_lower in terminal_name.lower():
                    logger.debug(f"[_is_terminal_station] {station.name} IS a terminal for line {check_line}")
                    return True

    logger.debug(f"[_is_terminal_station] {station.name} is NOT a terminal")
    return False


async def get_arrivals(query: ArrivalQuery) -> ArrivalResult:
    """Get train arrivals at a station."""
    logger.debug(f"[get_arrivals] Starting with query: {query}")

    # Resolve station name
    station = find_station_by_name(query.station)
    if not station:
        logger.error(f"[get_arrivals] Station not found: {query.station}")
        raise StationNotFoundError(query.station)

    logger.debug(f"[get_arrivals] Resolved station: {station.name}, lines: {station.lines}, gtfs_stop_ids: {station.gtfs_stop_ids}")

    # Determine which lines to query
    if query.line:
        requested_line = query.line.upper()
        if requested_line not in station.lines:
            raise ValueError(
                f"Line {requested_line} does not serve {station.name}. "
                f"Available lines: {', '.join(station.lines)}"
            )
        lines_to_query = [requested_line]
    else:
        lines_to_query = station.lines

    logger.debug(f"[get_arrivals] Lines to query: {lines_to_query}")

    # Parse direction
    gtfs_direction = parse_direction(query.direction, station, query.line) if query.direction else None
    logger.debug(f"[get_arrivals] Parsed direction: user_input={query.direction!r} -> gtfs_direction={gtfs_direction!r}")

    # At terminal stations, don't filter by direction - trains arrive with opposite direction
    # from what they depart as (e.g., trains arrive at South Ferry as 'S' but depart as 'N')
    if gtfs_direction and _is_terminal_station(station, query.line):
        logger.debug(f"[get_arrivals] Terminal station detected - ignoring direction filter")
        gtfs_direction = None

    # Get base stop ID
    base_stop_id = station.gtfs_stop_ids["N"].rstrip("N")
    logger.debug(f"[get_arrivals] Base stop ID: {base_stop_id}")

    # Fetch arrivals
    if query.line:
        logger.debug(f"[get_arrivals] Calling get_arrivals_at_stop(line={query.line}, stop_id={base_stop_id}, direction={gtfs_direction})")
        parsed_arrivals = await get_arrivals_at_stop(query.line, base_stop_id, gtfs_direction)
    else:
        logger.debug(f"[get_arrivals] Calling get_arrivals_at_stop_multi_line(lines={lines_to_query}, stop_id={base_stop_id}, direction={gtfs_direction})")
        parsed_arrivals = await get_arrivals_at_stop_multi_line(lines_to_query, base_stop_id, gtfs_direction)

    logger.debug(f"[get_arrivals] Got {len(parsed_arrivals)} parsed arrivals from GTFS")

    # Check if this is a terminal station - if so, we need to flip directions for display
    # (trains arrive with one direction but depart with the opposite)
    is_terminal = _is_terminal_station(station, query.line)

    # Convert to TrainArrival format
    arrivals: list[TrainArrival] = []
    for pa in parsed_arrivals:
        # At terminals, flip direction for display (arrival 'S' means departure 'N')
        display_direction: Literal["N", "S"] = pa.direction
        if is_terminal:
            display_direction = "N" if pa.direction == "S" else "S"
            logger.debug(f"[get_arrivals] Terminal station: flipping direction {pa.direction} -> {display_direction}")

        arrivals.append(TrainArrival(
            line=pa.route_id,
            direction=display_direction,
            direction_label=get_direction_label(display_direction, station, pa.route_id),
            destination=_get_terminal_name(pa.route_id, display_direction),
            arrival_time=pa.arrival_time,
            minutes_away=get_minutes_away(pa.arrival_time),
            is_express=is_express_line(pa.route_id),
            trip_id=pa.trip_id,
        ))

    # Sort by arrival time and apply limit
    sorted_arrivals = sorted(arrivals, key=lambda a: a.arrival_time)[:query.limit]

    return ArrivalResult(station=station, arrivals=sorted_arrivals, query=query)


async def get_arrivals_multi_line(
    station: Station,
    lines: list[str],
    direction: Optional[Literal["N", "S"]] = None,
) -> list[TrainArrival]:
    """Get arrivals for multiple lines at a station."""
    base_stop_id = station.gtfs_stop_ids["N"].rstrip("N")
    parsed_arrivals = await get_arrivals_at_stop_multi_line(lines, base_stop_id, direction)

    return [
        TrainArrival(
            line=pa.route_id,
            direction=pa.direction,
            direction_label=get_direction_label(pa.direction, station, pa.route_id),
            destination=_get_terminal_name(pa.route_id, pa.direction),
            arrival_time=pa.arrival_time,
            minutes_away=get_minutes_away(pa.arrival_time),
            is_express=is_express_line(pa.route_id),
            trip_id=pa.trip_id,
        )
        for pa in parsed_arrivals
    ]

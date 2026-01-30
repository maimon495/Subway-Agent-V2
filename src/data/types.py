"""Core data types for the NYC Subway Agent."""
from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import datetime

Borough = Literal["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]


@dataclass
class Station:
    id: str  # Internal ID: "union-square"
    name: str  # Display name: "14th St - Union Square"
    aliases: list[str]  # Search aliases
    gtfs_stop_ids: dict[str, str]  # {"N": "635N", "S": "635S"}
    lines: list[str]  # Lines serving this station
    is_express: dict[str, bool]  # Per-line express status
    borough: Borough
    complex_id: Optional[str] = None


@dataclass
class SubwayLine:
    id: str  # "4", "N", "A", etc.
    name: str  # "Lexington Avenue Express"
    color: str  # Hex color code
    feed_id: str  # Which GTFS-RT feed to use
    type: Literal["express", "local", "mixed"]
    division: Literal["IRT", "BMT", "IND"]


@dataclass
class TransferPoint:
    station_id: str
    station_name: str
    lines: dict[str, list[str]]  # {"express": ["4", "5"], "local": ["6"]}
    is_cross_platform: bool
    transfer_time_seconds: int
    notes: Optional[str] = None


@dataclass
class TrainArrival:
    line: str
    direction: Literal["N", "S"]
    direction_label: str
    destination: str
    arrival_time: datetime
    minutes_away: int
    is_express: bool
    trip_id: str


@dataclass
class TransferOption:
    transfer_station: Station
    local_line: str
    express_line: str
    local_arrival: datetime
    express_arrival: datetime
    wait_time_minutes: float
    time_savings_minutes: int
    stops_skipped: int
    recommendation: Literal["transfer", "stay"]
    reason: str


# GTFS-RT feed configuration
FEED_URLS: dict[str, str] = {
    "123456S": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "7": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "ACE": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "BDFM": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "NQRW": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "JZ": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "SIR": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
}

# Map each line to its feed
LINE_TO_FEED: dict[str, str] = {
    "1": "123456S", "2": "123456S", "3": "123456S",
    "4": "123456S", "5": "123456S", "6": "123456S",
    "7": "7", "S": "123456S",
    "A": "ACE", "C": "ACE", "E": "ACE",
    "B": "BDFM", "D": "BDFM", "F": "BDFM", "M": "BDFM",
    "N": "NQRW", "Q": "NQRW", "R": "NQRW", "W": "NQRW",
    "G": "G",
    "J": "JZ", "Z": "JZ",
    "L": "L",
    "SIR": "SIR",
}


def get_feed_url_for_line(line: str) -> str:
    """Get the GTFS-RT feed URL for a given subway line."""
    feed_id = LINE_TO_FEED.get(line.upper())
    if not feed_id:
        raise ValueError(f"Unknown line: {line}")
    return FEED_URLS[feed_id]

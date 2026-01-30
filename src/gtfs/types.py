"""GTFS-RT types for MTA subway feeds."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


@dataclass
class ParsedArrival:
    trip_id: str
    route_id: str
    direction: Literal["N", "S"]
    stop_id: str
    arrival_time: datetime
    departure_time: Optional[datetime] = None
    track: Optional[str] = None
    is_assigned: bool = False


@dataclass
class ParsedFeed:
    timestamp: datetime
    arrivals: list[ParsedArrival]

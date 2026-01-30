"""Direction parsing utilities for NYC Subway."""
import logging
from typing import Literal, Optional
from ..data.types import Station

logger = logging.getLogger(__name__)


def parse_direction(
    user_input: Optional[str],
    station: Station,
    line: Optional[str] = None,
) -> Optional[Literal["N", "S"]]:
    """Parse user direction input into GTFS direction (N/S)."""
    logger.debug(f"[parse_direction] Called with: user_input={user_input!r}, station={station.name}, line={line}")

    if not user_input:
        logger.debug("[parse_direction] No user_input, returning None")
        return None

    normalized = user_input.lower().strip()
    logger.debug(f"[parse_direction] Normalized input: {normalized!r}")

    # Universal mappings
    northbound = ["uptown", "north", "northbound", "the bronx", "bronx", "bronx-bound"]
    southbound = ["downtown", "south", "southbound"]

    if normalized in northbound:
        logger.debug(f"[parse_direction] Matched northbound: returning 'N'")
        return "N"
    if normalized in southbound:
        logger.debug(f"[parse_direction] Matched southbound: returning 'S'")
        return "S"

    # Context-dependent based on borough
    if station.borough == "Manhattan":
        if "brooklyn" in normalized:
            return "S"
        if "queens" in normalized:
            if line and line.upper() in ["7", "N", "W"]:
                return "N"
            if line and line.upper() in ["E", "F", "M", "R"]:
                return "S"

    elif station.borough == "Brooklyn":
        if "manhattan" in normalized:
            return "N"
        if "coney island" in normalized:
            return "S"

    elif station.borough == "Queens":
        if "manhattan" in normalized:
            return "S"
        if "flushing" in normalized:
            return "N"
        if "jamaica" in normalized:
            return "S"

    elif station.borough == "Bronx":
        if "manhattan" in normalized:
            return "S"

    # Line-specific terminal mappings
    if line:
        upper_line = line.upper()

        if upper_line == "7":
            if "flushing" in normalized or "main st" in normalized:
                return "N"
            if "hudson yards" in normalized or "34th" in normalized:
                return "S"

        if upper_line in ["N", "W"]:
            if "astoria" in normalized or "ditmars" in normalized:
                return "N"

        if upper_line == "Q":
            if "96th" in normalized or "second avenue" in normalized:
                return "N"
            if "coney island" in normalized or "brighton" in normalized:
                return "S"

    return None


def get_direction_label(
    direction: Literal["N", "S"],
    station: Station,
    line: Optional[str] = None,
) -> str:
    """Get a human-readable direction label for display."""
    if direction == "N":
        if line:
            upper_line = line.upper()
            if upper_line == "7":
                return "Flushing - Main St"
            if upper_line in ["N", "W"]:
                return "Astoria - Ditmars Blvd"
            if upper_line == "Q":
                return "96th St - Second Ave"
            if upper_line in ["1", "2", "3", "4", "5", "6"]:
                return "Uptown & The Bronx" if station.borough == "Manhattan" else "Manhattan"
            if upper_line in ["A", "C", "B", "D"]:
                return "Uptown & The Bronx"

        return "Uptown" if station.borough == "Manhattan" else "Manhattan-bound"

    # Southbound
    if line:
        upper_line = line.upper()
        if upper_line == "7":
            return "34th St - Hudson Yards"
        if upper_line in ["N", "Q", "R", "W", "1", "2", "3", "4", "5", "6"]:
            return "Downtown & Brooklyn" if station.borough == "Manhattan" else "Brooklyn"
        if upper_line in ["A", "C"]:
            return "Downtown & Brooklyn"
        if upper_line == "E":
            return "World Trade Center"
        if upper_line in ["B", "D", "F", "M"]:
            return "Downtown & Brooklyn"

    return "Downtown" if station.borough == "Manhattan" else "Brooklyn-bound"


def infer_direction(
    origin: Station,
    destination: Station,
    line: str,
) -> Optional[Literal["N", "S"]]:
    """Infer direction from origin and destination stations on the same line."""
    try:
        origin_id = int(origin.gtfs_stop_ids["N"].rstrip("NS"))
        dest_id = int(destination.gtfs_stop_ids["N"].rstrip("NS"))
    except ValueError:
        return None

    # For numbered lines (IRT), lower stop_id = more south
    if line.upper() in ["1", "2", "3", "4", "5", "6", "7"]:
        return "S" if dest_id < origin_id else "N"

    return None

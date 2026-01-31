"""Transfer analysis for local-to-express optimization."""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from ..data.types import Station, TransferOption, TransferPoint, TrainArrival
from ..data.stations import get_station_by_id, get_stations_for_line
from ..data.transfer_points import get_transfer_points_between
from ..data.lines import get_express_alternative
from ..gtfs.client import get_arrival_time_at_stop_for_trip
from ..utils.time import get_minutes_diff
from .arrival_service import get_arrivals_multi_line

logger = logging.getLogger(__name__)

MAX_EXPRESS_WAIT_MINUTES = 5  # Max time to wait for express after local arrives
MIN_STOPS_FOR_TRANSFER = 4


@dataclass
class TransferAnalysis:
    origin: Station
    destination: Station
    local_line: str
    direction: Literal["N", "S"]
    stops_to_destination: int
    possible_transfers: list[TransferOption]
    recommendation: Optional[TransferOption]
    no_transfer_arrival: Optional[str] = None


def _count_stops(from_station: Station, to_station: Station, line: str, direction: Literal["N", "S"]) -> int:
    """Count stops between two stations on a line."""
    stations_on_line = get_stations_for_line(line)
    from_index = next((i for i, s in enumerate(stations_on_line) if s.id == from_station.id), -1)
    to_index = next((i for i, s in enumerate(stations_on_line) if s.id == to_station.id), -1)

    if from_index == -1 or to_index == -1:
        return 10  # Default estimate

    return abs(to_index - from_index)


def _is_station_between(
    origin: Station,
    middle: Station,
    destination: Station,
    line: str,
    direction: Literal["N", "S"],
) -> bool:
    """Check if a station is between origin and destination."""
    stations_on_line = get_stations_for_line(line)
    origin_index = next((i for i, s in enumerate(stations_on_line) if s.id == origin.id), -1)
    middle_index = next((i for i, s in enumerate(stations_on_line) if s.id == middle.id), -1)
    dest_index = next((i for i, s in enumerate(stations_on_line) if s.id == destination.id), -1)

    if origin_index == -1 or middle_index == -1 or dest_index == -1:
        return middle.lines and line in middle.lines

    if direction == "N":
        return origin_index < middle_index < dest_index
    else:
        return origin_index > middle_index > dest_index


def _count_stops_skipped(
    transfer_station: Station,
    destination: Station,
    local_line: str,
    express_line: str,
    direction: Literal["N", "S"],
) -> int:
    """Count stops skipped by taking express vs local."""
    local_stops = _count_stops(transfer_station, destination, local_line, direction)
    express_stops = _count_stops(transfer_station, destination, express_line, direction)
    return max(0, local_stops - express_stops)


def _build_reason(net_savings: float, wait_time: float, stops_skipped: int, tp: TransferPoint) -> str:
    """Build a human-readable reason for the transfer recommendation."""
    if net_savings <= 0:
        if wait_time > 1.5:
            return f"Express wait ({round(wait_time)} min) outweighs time saved"
        return "Not enough stops remaining for express to help"

    parts = []
    if tp.is_cross_platform:
        parts.append("Cross-platform transfer")
    else:
        parts.append(f"{round(tp.transfer_time_seconds / 60)} min transfer walk")

    parts.append(f"skip {stops_skipped} stops")
    parts.append(f"save ~{round(net_savings)} min")

    return ", ".join(parts)


async def analyze_transfers(
    origin: Station,
    destination: Station,
    local_line: str,
    direction: Literal["N", "S"],
    boarding_train: Optional[TrainArrival] = None,
) -> TransferAnalysis:
    """Analyze potential local-to-express transfers for a route.

    Args:
        origin: Starting station
        destination: Ending station
        local_line: The local line to take
        direction: Direction of travel (N/S)
        boarding_train: The specific train the user will board at origin.
                       If provided, uses GTFS trip data to get exact arrival times.
    """
    logger.debug(f"[analyze_transfers] Starting analysis: {origin.name} -> {destination.name}, line={local_line}, dir={direction}")
    if boarding_train:
        logger.debug(f"[analyze_transfers] Boarding train: trip_id={boarding_train.trip_id}, departs origin at {boarding_train.arrival_time}")

    express_lines = get_express_alternative(local_line)

    if not express_lines:
        logger.debug(f"[analyze_transfers] No express alternative for {local_line}")
        return TransferAnalysis(
            origin=origin,
            destination=destination,
            local_line=local_line,
            direction=direction,
            stops_to_destination=_count_stops(origin, destination, local_line, direction),
            possible_transfers=[],
            recommendation=None,
        )

    # Get transfer points
    transfer_points = get_transfer_points_between(local_line, express_lines[0])
    logger.debug(f"[analyze_transfers] Found {len(transfer_points)} transfer points between {local_line} and {express_lines[0]}")

    # Filter to valid transfer points
    valid_transfer_points = []
    for tp in transfer_points:
        transfer_station = get_station_by_id(tp.station_id)
        if not transfer_station:
            continue

        if not _is_station_between(origin, transfer_station, destination, local_line, direction):
            logger.debug(f"[analyze_transfers] {transfer_station.name} not between origin and destination, skipping")
            continue

        stops_remaining = _count_stops(transfer_station, destination, local_line, direction)
        if stops_remaining <= MIN_STOPS_FOR_TRANSFER - 1:
            logger.debug(f"[analyze_transfers] {transfer_station.name} only {stops_remaining} stops from destination, skipping")
            continue

        valid_transfer_points.append(tp)

    logger.debug(f"[analyze_transfers] {len(valid_transfer_points)} valid transfer points")

    if not valid_transfer_points:
        return TransferAnalysis(
            origin=origin,
            destination=destination,
            local_line=local_line,
            direction=direction,
            stops_to_destination=_count_stops(origin, destination, local_line, direction),
            possible_transfers=[],
            recommendation=None,
        )

    # Analyze each transfer point
    possible_transfers: list[TransferOption] = []

    for tp in valid_transfer_points:
        transfer_station = get_station_by_id(tp.station_id)
        if not transfer_station:
            continue

        express_line = tp.lines["express"][0]
        transfer_stop_id = transfer_station.gtfs_stop_ids.get("N", "").rstrip("NS")

        # Get when the user's train arrives at the transfer station
        local_arrival_at_transfer = None

        if boarding_train and boarding_train.trip_id:
            # Try to use actual GTFS trip data to get exact arrival time at transfer station
            local_arrival_at_transfer = await get_arrival_time_at_stop_for_trip(
                local_line, boarding_train.trip_id, transfer_stop_id
            )

        if not local_arrival_at_transfer and boarding_train:
            # Fallback: estimate based on stops (2 min/stop)
            # This happens at terminal stations where the arriving trip_id differs from departing trip_id
            stops_to_transfer = _count_stops(origin, transfer_station, local_line, direction)
            from datetime import timedelta
            estimated_travel_time = timedelta(minutes=stops_to_transfer * 2)
            local_arrival_at_transfer = boarding_train.arrival_time + estimated_travel_time
            logger.debug(f"[analyze_transfers] Using estimated arrival at {transfer_station.name}: {local_arrival_at_transfer} ({stops_to_transfer} stops * 2 min)")
        elif local_arrival_at_transfer:
            logger.debug(f"[analyze_transfers] Train {boarding_train.trip_id} arrives at {transfer_station.name} at {local_arrival_at_transfer}")

        if not local_arrival_at_transfer:
            logger.warning(f"[analyze_transfers] No boarding train provided, cannot calculate transfer timing")
            continue

        # Get express arrivals at transfer station AFTER local arrives
        express_arrivals = await get_arrivals_multi_line(transfer_station, [express_line], direction)

        # Find the next express that arrives after the local
        next_express = None
        for exp in express_arrivals:
            time_after_local = (exp.arrival_time - local_arrival_at_transfer).total_seconds() / 60
            if time_after_local >= 0:
                next_express = exp
                logger.debug(f"[analyze_transfers] Found express {exp.line} arriving {time_after_local:.1f} min after local at {transfer_station.name}")
                break

        if not next_express:
            logger.debug(f"[analyze_transfers] No express found after local at {transfer_station.name}")
            continue

        wait_time_minutes = (next_express.arrival_time - local_arrival_at_transfer).total_seconds() / 60

        # Calculate arrival at destination for both scenarios
        # Get destination stop ID
        dest_stop_id = destination.gtfs_stop_ids.get("N", "").rstrip("NS")

        # Scenario A: Stay on local - get arrival time at destination from same trip
        local_arrival_at_dest = await get_arrival_time_at_stop_for_trip(
            local_line, boarding_train.trip_id, dest_stop_id
        )

        # Scenario B: Transfer to express - get arrival time at destination from express trip
        express_arrival_at_dest = None
        if next_express.trip_id:
            express_arrival_at_dest = await get_arrival_time_at_stop_for_trip(
                express_line, next_express.trip_id, dest_stop_id
            )

        # Calculate actual time savings
        if local_arrival_at_dest and express_arrival_at_dest:
            # Add transfer walk time to express scenario
            transfer_walk_minutes = tp.transfer_time_seconds / 60
            effective_express_arrival = express_arrival_at_dest
            # Note: transfer walk time is already accounted for in waiting for the express

            time_savings = (local_arrival_at_dest - express_arrival_at_dest).total_seconds() / 60
            logger.debug(f"[analyze_transfers] Stay on local: arrive {local_arrival_at_dest}")
            logger.debug(f"[analyze_transfers] Transfer to express: arrive {express_arrival_at_dest}")
            logger.debug(f"[analyze_transfers] Time savings: {time_savings:.1f} min")
        else:
            # Fallback to stop-based estimate
            stops_skipped = _count_stops_skipped(
                transfer_station, destination, local_line, express_line, direction
            )
            time_saved_from_express = stops_skipped * 2
            transfer_penalty = (tp.transfer_time_seconds / 60) + wait_time_minutes
            time_savings = time_saved_from_express - transfer_penalty
            logger.debug(f"[analyze_transfers] Using estimated savings: {time_savings:.1f} min (skipping {stops_skipped} stops)")

        stops_skipped = _count_stops_skipped(
            transfer_station, destination, local_line, express_line, direction
        )

        possible_transfers.append(TransferOption(
            transfer_station=transfer_station,
            local_line=local_line,
            express_line=express_line,
            local_arrival=local_arrival_at_transfer,
            express_arrival=next_express.arrival_time,
            wait_time_minutes=round(wait_time_minutes, 1),
            time_savings_minutes=round(time_savings),
            stops_skipped=stops_skipped,
            recommendation="transfer" if time_savings >= 2 else "stay",
            reason=_build_reason(time_savings, wait_time_minutes, stops_skipped, tp),
            local_dest_arrival=local_arrival_at_dest,
            express_dest_arrival=express_arrival_at_dest,
        ))

    # Sort by time savings
    possible_transfers.sort(key=lambda t: t.time_savings_minutes, reverse=True)

    recommendation = next((t for t in possible_transfers if t.recommendation == "transfer"), None)

    return TransferAnalysis(
        origin=origin,
        destination=destination,
        local_line=local_line,
        direction=direction,
        stops_to_destination=_count_stops(origin, destination, local_line, direction),
        possible_transfers=possible_transfers,
        recommendation=recommendation,
    )

"""Transfer analysis for local-to-express optimization."""
from dataclasses import dataclass
from typing import Literal, Optional

from ..data.types import Station, TransferOption, TransferPoint
from ..data.stations import get_station_by_id, get_stations_for_line
from ..data.transfer_points import get_transfer_points_between
from ..data.lines import get_express_alternative
from ..utils.time import get_minutes_diff
from .arrival_service import get_arrivals_multi_line

TRANSFER_WINDOW_MS = 2 * 60 * 1000  # 2 minutes
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
) -> TransferAnalysis:
    """Analyze potential local-to-express transfers for a route."""
    express_lines = get_express_alternative(local_line)

    if not express_lines:
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

    # Filter to valid transfer points
    valid_transfer_points = []
    for tp in transfer_points:
        transfer_station = get_station_by_id(tp.station_id)
        if not transfer_station:
            continue

        if not _is_station_between(origin, transfer_station, destination, local_line, direction):
            continue

        stops_remaining = _count_stops(transfer_station, destination, local_line, direction)
        if stops_remaining <= MIN_STOPS_FOR_TRANSFER - 1:
            continue

        valid_transfer_points.append(tp)

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

        # Get real-time arrivals
        local_arrivals = await get_arrivals_multi_line(transfer_station, [local_line], direction)
        express_arrivals = await get_arrivals_multi_line(transfer_station, [express_line], direction)

        # Find matching pairs within transfer window
        for local in local_arrivals[:3]:
            for exp in express_arrivals:
                diff_ms = (exp.arrival_time - local.arrival_time).total_seconds() * 1000
                if 0 < diff_ms <= TRANSFER_WINDOW_MS:
                    wait_time_minutes = get_minutes_diff(exp.arrival_time, local.arrival_time)

                    stops_skipped = _count_stops_skipped(
                        transfer_station, destination, local_line, express_line, direction
                    )

                    time_saved_from_express = stops_skipped * 2
                    transfer_penalty = (tp.transfer_time_seconds / 60) + wait_time_minutes
                    net_savings = time_saved_from_express - transfer_penalty

                    possible_transfers.append(TransferOption(
                        transfer_station=transfer_station,
                        local_line=local_line,
                        express_line=express_line,
                        local_arrival=local.arrival_time,
                        express_arrival=exp.arrival_time,
                        wait_time_minutes=wait_time_minutes,
                        time_savings_minutes=round(net_savings),
                        stops_skipped=stops_skipped,
                        recommendation="transfer" if net_savings > 0 else "stay",
                        reason=_build_reason(net_savings, wait_time_minutes, stops_skipped, tp),
                    ))
                    break

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

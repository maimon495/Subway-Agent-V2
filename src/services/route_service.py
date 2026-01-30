"""Route planning service with transfer optimization."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, Optional

from ..data.types import Station
from ..data.stations import find_station_by_name
from ..data.lines import is_express_line, get_trunk_line
from ..utils.time import format_time
from .arrival_service import get_arrivals_multi_line
from .transfer_analyzer import analyze_transfers, TransferAnalysis
from .direction_parser import infer_direction


@dataclass
class RouteOption:
    type: Literal["no-transfer", "with-transfer"]
    description: str
    line: str
    express_line: Optional[str] = None
    transfer_at: Optional[Station] = None
    estimated_arrival: Optional[datetime] = None
    time_saved: Optional[int] = None
    details: list[str] = field(default_factory=list)


@dataclass
class RouteResult:
    origin: Station
    destination: Station
    direct_lines: list[str]
    direction: Literal["N", "S"]
    transfer_analysis: Optional[TransferAnalysis]
    recommendation: str
    options: list[RouteOption]


def _find_direct_lines(origin: Station, destination: Station) -> list[str]:
    """Find lines that directly connect two stations."""
    origin_lines = set(origin.lines)
    dest_lines = set(destination.lines)

    # Find intersection
    direct_lines = list(origin_lines & dest_lines)

    # Also check if they're on the same trunk
    origin_trunks = [get_trunk_line(l) for l in origin.lines]
    dest_trunks = [get_trunk_line(l) for l in destination.lines]

    for trunk in origin_trunks:
        if trunk and trunk in dest_trunks:
            local_lines = [l for l in origin.lines if not is_express_line(l) and get_trunk_line(l) == trunk]
            for line in local_lines:
                if line not in direct_lines:
                    direct_lines.append(line)

    return direct_lines


def _estimate_arrival_time(departure_time: datetime, stops: int = 10) -> datetime:
    """Estimate arrival time based on stops (rough: 2 min/stop)."""
    travel_time = timedelta(minutes=stops * 2)
    return departure_time + travel_time


async def get_route(origin_name: str, destination_name: str) -> RouteResult:
    """Get route recommendations between two stations."""
    # Resolve station names
    origin = find_station_by_name(origin_name)
    if not origin:
        raise ValueError(f'Origin station not found: "{origin_name}"')

    destination = find_station_by_name(destination_name)
    if not destination:
        raise ValueError(f'Destination station not found: "{destination_name}"')

    # Find direct lines
    direct_lines = _find_direct_lines(origin, destination)

    if not direct_lines:
        raise ValueError(
            f"No direct route found between {origin.name} and {destination.name}. "
            "A transfer may be required."
        )

    # Determine direction
    primary_line = direct_lines[0]
    direction = infer_direction(origin, destination, primary_line) or "N"

    # Check if starting on local-only station
    is_origin_local_only = all(not is_express_line(line) for line in direct_lines)
    is_destination_express = any(
        is_express_line(line) and destination.is_express.get(line, False)
        for line in direct_lines
    )

    # Analyze transfer opportunities
    transfer_analysis: Optional[TransferAnalysis] = None
    if is_origin_local_only and is_destination_express:
        local_line = next((l for l in direct_lines if not is_express_line(l)), None)
        if local_line:
            transfer_analysis = await analyze_transfers(origin, destination, local_line, direction)

    # Build route options
    options: list[RouteOption] = []

    # Option A: No transfer
    no_transfer_line = next((l for l in direct_lines if not is_express_line(l)), direct_lines[0])
    local_arrivals = await get_arrivals_multi_line(origin, [no_transfer_line], direction)
    next_local = local_arrivals[0] if local_arrivals else None

    options.append(RouteOption(
        type="no-transfer",
        description=f"Stay on {no_transfer_line} train",
        line=no_transfer_line,
        estimated_arrival=_estimate_arrival_time(next_local.arrival_time) if next_local else None,
        details=[
            f"Take {no_transfer_line} {'uptown' if direction == 'N' else 'downtown'}",
            f"Next train: {format_time(next_local.arrival_time)}" if next_local else "Check real-time data for next train",
        ],
    ))

    # Option B: With transfer (if recommended)
    if transfer_analysis and transfer_analysis.recommendation:
        rec = transfer_analysis.recommendation
        options.append(RouteOption(
            type="with-transfer",
            description=f"Transfer at {rec.transfer_station.name}",
            line=rec.local_line,
            express_line=rec.express_line,
            transfer_at=rec.transfer_station,
            estimated_arrival=rec.express_arrival + timedelta(minutes=5),  # Rough estimate
            time_saved=rec.time_savings_minutes,
            details=[
                f"Take {rec.local_line} to {rec.transfer_station.name}",
                f"Transfer to {rec.express_line} express",
                f"Express arrives {round(rec.wait_time_minutes)} min after local",
                f"Saves ~{rec.time_savings_minutes} minutes",
                rec.reason,
            ],
        ))

    # Build recommendation text
    if transfer_analysis and transfer_analysis.recommendation and transfer_analysis.recommendation.time_savings_minutes >= 2:
        rec = transfer_analysis.recommendation
        recommendation = (
            f"Transfer at {rec.transfer_station.name} "
            f"from {rec.local_line} to {rec.express_line} "
            f"to save ~{rec.time_savings_minutes} minutes."
        )
    else:
        recommendation = f"Stay on the {no_transfer_line} train. No significant time savings from transferring."

    return RouteResult(
        origin=origin,
        destination=destination,
        direct_lines=direct_lines,
        direction=direction,
        transfer_analysis=transfer_analysis,
        recommendation=recommendation,
        options=options,
    )

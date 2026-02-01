"""Route planning service with transfer optimization."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, Optional

from ..data.types import Station
from ..data.stations import find_station_by_name
from ..data.lines import is_express_line, get_trunk_line
from ..gtfs.client import get_arrival_time_at_stop_for_trip
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

    # Check if starting on local-only station and destination has express service
    is_origin_local_only = all(not is_express_line(line) for line in direct_lines)
    # Check if destination has ANY express service (not just on direct lines)
    # This determines if a local-to-express transfer is even possible
    is_destination_express = any(
        is_express_line(line) and destination.is_express.get(line, False)
        for line in destination.lines
    )

    # Get the local line and next train at origin FIRST
    # This train will be used for all time calculations
    no_transfer_line = next((l for l in direct_lines if not is_express_line(l)), direct_lines[0])
    local_arrivals = await get_arrivals_multi_line(origin, [no_transfer_line], direction)
    next_local = local_arrivals[0] if local_arrivals else None

    # Analyze transfer opportunities - pass the boarding train for accurate timing
    transfer_analysis: Optional[TransferAnalysis] = None
    if is_origin_local_only and is_destination_express and next_local:
        local_line = next((l for l in direct_lines if not is_express_line(l)), None)
        if local_line:
            transfer_analysis = await analyze_transfers(
                origin, destination, local_line, direction,
                boarding_train=next_local  # Pass the specific train we're boarding
            )

    # Build route options
    options: list[RouteOption] = []

    # Get actual arrival time at destination for no-transfer option
    local_dest_arrival = None
    if next_local and next_local.trip_id:
        dest_stop_id = destination.gtfs_stop_ids.get("N", "").rstrip("NS")
        local_dest_arrival = await get_arrival_time_at_stop_for_trip(
            no_transfer_line, next_local.trip_id, dest_stop_id
        )

    # Use actual arrival time if available, otherwise estimate based on stops
    if local_dest_arrival:
        no_transfer_arrival = local_dest_arrival
    elif next_local:
        # Estimate travel time using GTFS stop ID difference (works for IRT lines with numeric IDs)
        # or fall back to a reasonable minimum
        origin_stop_id = origin.gtfs_stop_ids.get(direction, origin.gtfs_stop_ids.get("N", ""))
        dest_stop_id = destination.gtfs_stop_ids.get(direction, destination.gtfs_stop_ids.get("N", ""))

        # Extract numeric portion of stop IDs
        origin_num = ''.join(c for c in origin_stop_id if c.isdigit())
        dest_num = ''.join(c for c in dest_stop_id if c.isdigit())

        if origin_num and dest_num and origin_num.isdigit() and dest_num.isdigit():
            # For IRT lines, stop IDs are sequential - difference gives approximate stop count
            stops_to_dest = abs(int(origin_num) - int(dest_num))
            # Ensure at least 5 stops as sanity check for any real trip
            stops_to_dest = max(stops_to_dest, 5)
        else:
            # Fallback for lines with non-numeric stop IDs
            stops_to_dest = 10  # Conservative estimate

        no_transfer_arrival = next_local.arrival_time + timedelta(minutes=stops_to_dest * 2)
    else:
        no_transfer_arrival = None

    no_transfer_details = [
        f"Take {no_transfer_line} {'uptown' if direction == 'N' else 'downtown'}",
        f"Board at: {format_time(next_local.arrival_time)}" if next_local else "Check real-time data for next train",
    ]
    if no_transfer_arrival:
        no_transfer_details.append(f"Arrive at destination: {format_time(no_transfer_arrival)}")

    options.append(RouteOption(
        type="no-transfer",
        description=f"Stay on {no_transfer_line} train",
        line=no_transfer_line,
        estimated_arrival=no_transfer_arrival,
        details=no_transfer_details,
    ))

    # Option B: With transfer (if analysis found any viable transfer)
    # Show even if not recommended, so user can see both options
    best_transfer = None
    if transfer_analysis:
        # Use recommendation if exists, otherwise use best available transfer
        best_transfer = transfer_analysis.recommendation or (
            transfer_analysis.possible_transfers[0] if transfer_analysis.possible_transfers else None
        )

    if best_transfer:
        rec = best_transfer

        # Use actual arrival time at destination if available
        transfer_dest_arrival = rec.express_dest_arrival or (
            rec.express_arrival + timedelta(minutes=5)  # Fallback estimate
        )

        transfer_details = [
            f"Take {rec.local_line} to {rec.transfer_station.name}",
            f"Arrive at transfer: {format_time(rec.local_arrival)}",
        ]
        # Show wait time for express
        if rec.wait_time_minutes <= 1:
            transfer_details.append(f"Transfer to {rec.express_line} express (arrives {format_time(rec.express_arrival)})")
        else:
            transfer_details.append(f"Wait {round(rec.wait_time_minutes)} min for {rec.express_line} express (arrives {format_time(rec.express_arrival)})")

        if transfer_dest_arrival:
            transfer_details.append(f"Arrive at destination: {format_time(transfer_dest_arrival)}")
        if rec.time_savings_minutes > 0:
            transfer_details.append(f"Saves ~{rec.time_savings_minutes} minutes")
        elif rec.time_savings_minutes < 0:
            transfer_details.append(f"Takes ~{abs(rec.time_savings_minutes)} minutes longer than local")

        options.append(RouteOption(
            type="with-transfer",
            description=f"Transfer at {rec.transfer_station.name}",
            line=rec.local_line,
            express_line=rec.express_line,
            transfer_at=rec.transfer_station,
            estimated_arrival=transfer_dest_arrival,
            time_saved=rec.time_savings_minutes,
            details=transfer_details,
        ))

    # Build recommendation text with actual arrival times
    if transfer_analysis and transfer_analysis.recommendation and transfer_analysis.recommendation.time_savings_minutes >= 2:
        rec = transfer_analysis.recommendation
        transfer_arrival = rec.express_dest_arrival
        recommendation = (
            f"Transfer at {rec.transfer_station.name} "
            f"from {rec.local_line} to {rec.express_line} "
            f"to save ~{rec.time_savings_minutes} minutes. "
        )
        if transfer_arrival and no_transfer_arrival:
            recommendation += (
                f"Arrive at {format_time(transfer_arrival)} vs {format_time(no_transfer_arrival)} if you stay on local."
            )
    else:
        recommendation = f"Stay on the {no_transfer_line} train. No significant time savings from transferring."
        if no_transfer_arrival:
            recommendation += f" Arrive at {format_time(no_transfer_arrival)}."

    return RouteResult(
        origin=origin,
        destination=destination,
        direct_lines=direct_lines,
        direction=direction,
        transfer_analysis=transfer_analysis,
        recommendation=recommendation,
        options=options,
    )

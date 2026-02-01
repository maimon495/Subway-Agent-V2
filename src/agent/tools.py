"""LangChain tools for the NYC Subway Agent."""
import asyncio
import logging
from typing import Optional, Union

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

from ..data.stations import find_stations_by_name
from ..services.arrival_service import get_arrivals, ArrivalQuery, StationNotFoundError
from ..services.route_service import get_route
from ..services.alert_service import get_alerts_for_lines, get_all_alerts, get_service_summary
from ..utils.time import format_time


def _run_async(coro):
    """Run an async coroutine in the current event loop or create a new one."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're in an async context, create a new thread to run the coroutine
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


@tool
def get_next_trains(
    station: str,
    line: Optional[str] = None,
    direction: Optional[str] = None,
    limit: Union[int, str] = 5,
) -> dict:
    """Get real-time train arrivals at a NYC subway station.

    Args:
        station: Station name, e.g., "Union Square", "Times Square", "Penn Station"
        line: Specific subway line letter or number, e.g., "N", "4", "A", "L"
        direction: Travel direction - uptown/downtown for Manhattan, or borough-bound
        limit: Maximum number of arrivals to return (default: 5)

    Returns:
        Dictionary with arrival information or error details
    """
    # Handle LLM sending limit as string
    if isinstance(limit, str):
        limit = int(limit)

    # Check for ambiguous station names - if multiple matches exist, ask for clarification
    matches = find_stations_by_name(station, limit=5)
    if len(matches) > 1:
        # Check if top match is significantly better than alternatives
        # If names are very similar or query is short/generic, show alternatives
        query_normalized = station.lower().strip()
        top_match = matches[0]

        # If query doesn't exactly match the top result, show alternatives
        exact_match = (top_match.name.lower() == query_normalized or
                      any(a.lower() == query_normalized for a in top_match.aliases))

        if not exact_match:
            # Return alternatives for clarification
            alternatives = [
                {"name": s.name, "lines": s.lines, "borough": s.borough}
                for s in matches[:4]
            ]
            return {
                "success": True,
                "needs_clarification": True,
                "message": f'Multiple stations match "{station}". Please clarify which station:',
                "alternatives": alternatives,
            }

    # Parse slash-separated lines (e.g., "2/3" -> ["2", "3"])
    lines_to_query = None
    if line:
        if "/" in line:
            lines_to_query = [l.strip().upper() for l in line.split("/")]
        else:
            lines_to_query = [line.strip().upper()]

    logger.debug(f"[get_next_trains] Called with: station={station!r}, line={line!r}, parsed_lines={lines_to_query!r}, direction={direction!r}, limit={limit}")
    try:
        # Query for first line to get station info, then filter results
        first_line = lines_to_query[0] if lines_to_query else None
        query = ArrivalQuery(station=station, line=first_line, direction=direction, limit=limit * 2 if lines_to_query and len(lines_to_query) > 1 else limit)
        logger.debug(f"[get_next_trains] Created query: {query}")
        result = _run_async(get_arrivals(query))

        # If multiple lines requested, also query for other lines and merge
        if lines_to_query and len(lines_to_query) > 1:
            all_arrivals = list(result.arrivals)
            for extra_line in lines_to_query[1:]:
                try:
                    extra_query = ArrivalQuery(station=station, line=extra_line, direction=direction, limit=limit)
                    extra_result = _run_async(get_arrivals(extra_query))
                    all_arrivals.extend(extra_result.arrivals)
                except Exception:
                    pass  # Line might not serve this station
            # Sort by arrival time and limit
            all_arrivals.sort(key=lambda a: a.arrival_time)
            result.arrivals = all_arrivals[:limit]
        logger.debug(f"[get_next_trains] Got {len(result.arrivals)} arrivals for station {result.station.name}")

        if not result.arrivals:
            logger.warning(f"[get_next_trains] NO ARRIVALS found for station={station}, line={line}, direction={direction}")
            return {
                "success": True,
                "station": result.station.name,
                "message": f"No upcoming trains found at {result.station.name}"
                    + (f" for the {line} train" if line else "")
                    + (f" going {direction}" if direction else "") + ".",
                "arrivals": [],
            }

        # Get service alerts for lines at this station
        lines_to_check = lines_to_query if lines_to_query else result.station.lines
        service_alerts = []
        try:
            alerts = _run_async(get_alerts_for_lines(lines_to_check))

            # Get GTFS stop IDs for this station to filter elevator alerts
            station_stop_ids = {s.rstrip("NS") for s in result.station.gtfs_stop_ids.values()}

            filtered_alerts = []
            for a in alerts:
                # Check if this is an elevator/escalator outage
                header_lower = a.header_text.lower()
                is_elevator_alert = "elevator" in header_lower or "escalator" in header_lower

                if is_elevator_alert:
                    # Only include if it affects this station
                    alert_stop_ids = {s.rstrip("NS") for s in a.affected_stops}
                    if alert_stop_ids & station_stop_ids:
                        filtered_alerts.append(a)
                else:
                    # Non-elevator alerts are always included
                    filtered_alerts.append(a)

            service_alerts = [
                {"lines": a.affected_lines, "header": a.header_text, "effect": a.effect}
                for a in filtered_alerts[:3]
            ]
        except Exception:
            pass

        return {
            "success": True,
            "station": result.station.name,
            "lines": list(set(a.line for a in result.arrivals)),
            "arrivals": [
                {
                    "line": a.line,
                    "direction": a.direction_label,
                    "destination": a.destination,
                    "minutes_away": a.minutes_away,
                    "arrival_time": format_time(a.arrival_time),
                    "is_express": a.is_express,
                }
                for a in result.arrivals
            ],
            "service_alerts": service_alerts if service_alerts else None,
        }

    except StationNotFoundError:
        suggestions = find_stations_by_name(station, 3)
        return {
            "success": False,
            "error": f'Station "{station}" not found.',
            "suggestions": [s.name for s in suggestions] if suggestions else ["Try a different station name"],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _check_ambiguous_station(station_query: str, label: str) -> Optional[dict]:
    """Check if a station query is ambiguous and needs clarification."""
    matches = find_stations_by_name(station_query, limit=5)
    if len(matches) > 1:
        query_normalized = station_query.lower().strip()
        top_match = matches[0]

        # If query doesn't exactly match the top result, show alternatives
        exact_match = (top_match.name.lower() == query_normalized or
                      any(a.lower() == query_normalized for a in top_match.aliases))

        if not exact_match:
            alternatives = [
                {"name": s.name, "lines": s.lines, "borough": s.borough}
                for s in matches[:4]
            ]
            return {
                "success": True,
                "needs_clarification": True,
                "clarification_for": label,
                "message": f'Multiple stations match "{station_query}". Please clarify which {label}:',
                "alternatives": alternatives,
            }
    return None


@tool
def get_route_recommendation(origin: str, destination: str) -> dict:
    """Get route recommendations between two NYC subway stations.

    Analyzes local-to-express transfer opportunities and recommends the fastest route
    based on real-time train arrival data.

    Args:
        origin: Starting station name, e.g., "South Ferry", "14th Street"
        destination: Destination station name, e.g., "Penn Station", "Grand Central"

    Returns:
        Dictionary with route options and recommendation
    """
    # Check for ambiguous origin
    origin_ambiguity = _check_ambiguous_station(origin, "origin station")
    if origin_ambiguity:
        return origin_ambiguity

    # Check for ambiguous destination
    dest_ambiguity = _check_ambiguous_station(destination, "destination station")
    if dest_ambiguity:
        return dest_ambiguity

    try:
        result = _run_async(get_route(origin, destination))

        # Get service alerts for the lines involved
        service_alerts = None
        try:
            alerts = _run_async(get_alerts_for_lines(result.direct_lines))
            if alerts:
                # Get GTFS stop IDs for origin and destination to filter elevator alerts
                origin_stop_ids = set(result.origin.gtfs_stop_ids.values())
                dest_stop_ids = set(result.destination.gtfs_stop_ids.values())
                # Strip N/S suffixes for matching
                relevant_stop_ids = {s.rstrip("NS") for s in origin_stop_ids | dest_stop_ids}

                filtered_alerts = []
                for a in alerts:
                    # Check if this is an elevator/escalator outage
                    header_lower = a.header_text.lower()
                    is_elevator_alert = "elevator" in header_lower or "escalator" in header_lower

                    if is_elevator_alert:
                        # Only include if it affects origin or destination station
                        alert_stop_ids = {s.rstrip("NS") for s in a.affected_stops}
                        if alert_stop_ids & relevant_stop_ids:
                            filtered_alerts.append(a)
                    else:
                        # Non-elevator alerts are always included
                        filtered_alerts.append(a)

                if filtered_alerts:
                    service_alerts = [
                        {"lines": a.affected_lines, "header": a.header_text, "effect": a.effect}
                        for a in filtered_alerts[:3]
                    ]
        except Exception:
            pass

        # Build a clear comparison of options
        options_summary = []
        for opt in result.options:
            if opt.type == "no-transfer":
                options_summary.append({
                    "option": "A",
                    "label": f"No transfer - Stay on {opt.line} train",
                    "arrive_destination": format_time(opt.estimated_arrival) if opt.estimated_arrival else "Unknown",
                    "details": opt.details,
                })
            else:
                options_summary.append({
                    "option": "B",
                    "label": f"Transfer at {opt.transfer_at.name}: {opt.line} → {opt.express_line}",
                    "arrive_destination": format_time(opt.estimated_arrival) if opt.estimated_arrival else "Unknown",
                    "time_saved_minutes": opt.time_saved,
                    "details": opt.details,
                })

        return {
            "success": True,
            "origin": result.origin.name,
            "destination": result.destination.name,
            "direct_lines": result.direct_lines,
            "direction": "uptown/northbound" if result.direction == "N" else "downtown/southbound",
            "recommendation": result.recommendation,
            "options": options_summary,
            "service_alerts": service_alerts,
        }

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            is_origin_error = "Origin" in error_msg
            search_term = origin if is_origin_error else destination
            suggestions = find_stations_by_name(search_term, 3)
            return {
                "success": False,
                "error": error_msg,
                "suggestions": {
                    "for": "origin" if is_origin_error else "destination",
                    "stations": [s.name for s in suggestions],
                } if suggestions else None,
            }
        return {"success": False, "error": error_msg}

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_service_alerts(lines: Optional[list[str]] = None, summary_only: bool = False) -> dict:
    """Get current NYC subway service alerts and delays.

    Args:
        lines: Specific lines to check, e.g., ["N", "Q", "R", "W"]. If omitted, returns all alerts.
        summary_only: If true, returns just a summary of good service vs delays/suspensions

    Returns:
        Dictionary with alert information
    """
    try:
        if summary_only:
            summary = _run_async(get_service_summary())
            return {
                "success": True,
                "summary": {
                    "good_service": summary["good_service"],
                    "delays": summary["delays"],
                    "suspended": summary["suspended"],
                    "alert_count": len(summary["alerts"]),
                },
            }

        if lines:
            alerts = _run_async(get_alerts_for_lines(lines))
        else:
            alerts = _run_async(get_all_alerts())

        if not alerts:
            return {
                "success": True,
                "message": f"Good service on {', '.join(lines)} lines" if lines else "Good service on all lines",
                "alerts": [],
            }

        effect_labels = {
            "NO_SERVICE": "No Service",
            "REDUCED_SERVICE": "Reduced Service",
            "SIGNIFICANT_DELAYS": "Significant Delays",
            "DETOUR": "Detour",
            "ADDITIONAL_SERVICE": "Additional Service",
            "MODIFIED_SERVICE": "Modified Service",
            "OTHER_EFFECT": "Service Change",
            "UNKNOWN_EFFECT": "Alert",
            "STOP_MOVED": "Stop Relocated",
        }

        return {
            "success": True,
            "alert_count": len(alerts),
            "alerts": [
                {
                    "lines": a.affected_lines,
                    "header": a.header_text,
                    "description": a.description_text,
                    "effect": effect_labels.get(a.effect, a.effect),
                    "cause": a.cause,
                }
                for a in alerts
            ],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Export all tools
ALL_TOOLS = [get_next_trains, get_route_recommendation, get_service_alerts]

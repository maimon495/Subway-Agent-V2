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

    logger.debug(f"[get_next_trains] Called with: station={station!r}, line={line!r}, direction={direction!r}, limit={limit}")
    try:
        query = ArrivalQuery(station=station, line=line, direction=direction, limit=limit)
        logger.debug(f"[get_next_trains] Created query: {query}")
        result = _run_async(get_arrivals(query))
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
        lines_to_check = [line] if line else result.station.lines
        service_alerts = []
        try:
            alerts = _run_async(get_alerts_for_lines(lines_to_check))
            service_alerts = [
                {"lines": a.affected_lines, "header": a.header_text, "effect": a.effect}
                for a in alerts[:3]
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
    try:
        result = _run_async(get_route(origin, destination))

        # Get service alerts for the lines involved
        service_alerts = None
        try:
            alerts = _run_async(get_alerts_for_lines(result.direct_lines))
            if alerts:
                service_alerts = [
                    {"lines": a.affected_lines, "header": a.header_text, "effect": a.effect}
                    for a in alerts[:3]
                ]
        except Exception:
            pass

        return {
            "success": True,
            "origin": result.origin.name,
            "destination": result.destination.name,
            "direct_lines": result.direct_lines,
            "direction": "uptown/northbound" if result.direction == "N" else "downtown/southbound",
            "recommendation": result.recommendation,
            "options": [
                {
                    "type": opt.type,
                    "description": opt.description,
                    "line": opt.line,
                    "express_line": opt.express_line,
                    "transfer_at": opt.transfer_at.name if opt.transfer_at else None,
                    "estimated_arrival": format_time(opt.estimated_arrival) if opt.estimated_arrival else None,
                    "time_saved": opt.time_saved,
                    "details": opt.details,
                }
                for opt in result.options
            ],
            "transfer_analysis": {
                "has_recommended_transfer": result.transfer_analysis.recommendation is not None,
                "transfer_station": result.transfer_analysis.recommendation.transfer_station.name if result.transfer_analysis and result.transfer_analysis.recommendation else None,
                "local_line": result.transfer_analysis.local_line if result.transfer_analysis else None,
                "express_line": result.transfer_analysis.recommendation.express_line if result.transfer_analysis and result.transfer_analysis.recommendation else None,
                "wait_time": result.transfer_analysis.recommendation.wait_time_minutes if result.transfer_analysis and result.transfer_analysis.recommendation else None,
                "time_saved": result.transfer_analysis.recommendation.time_savings_minutes if result.transfer_analysis and result.transfer_analysis.recommendation else None,
            } if result.transfer_analysis else None,
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

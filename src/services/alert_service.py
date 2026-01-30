"""Service alert handling for NYC Subway."""
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from google.transit import gtfs_realtime_pb2

ALERTS_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts"

# Cache for alerts (5 minute TTL)
_alerts_cache: Optional[tuple[list["ServiceAlert"], float]] = None
CACHE_TTL_SECONDS = 5 * 60


@dataclass
class ServiceAlert:
    id: str
    header_text: str
    description_text: str
    affected_lines: list[str]
    affected_stops: list[str]
    cause: str
    effect: str
    active_periods: list[dict]
    is_active: bool


CAUSE_MAP: dict[int, str] = {
    1: "Unknown", 2: "Other", 3: "Technical Problem", 4: "Strike",
    5: "Demonstration", 6: "Accident", 7: "Holiday", 8: "Weather",
    9: "Maintenance", 10: "Construction", 11: "Police Activity", 12: "Medical Emergency",
}

EFFECT_MAP: dict[int, str] = {
    1: "NO_SERVICE", 2: "REDUCED_SERVICE", 3: "SIGNIFICANT_DELAYS", 4: "DETOUR",
    5: "ADDITIONAL_SERVICE", 6: "MODIFIED_SERVICE", 7: "OTHER_EFFECT",
    8: "UNKNOWN_EFFECT", 9: "STOP_MOVED",
}


def _extract_text(translated_string) -> str:
    """Extract text from TranslatedString."""
    if not translated_string or not translated_string.translation:
        return ""
    for t in translated_string.translation:
        if t.language in ("en", "EN"):
            text = t.text
            break
    else:
        text = translated_string.translation[0].text if translated_string.translation else ""

    # Clean up HTML entities
    return (text
        .replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .strip())


async def fetch_service_alerts() -> list[ServiceAlert]:
    """Fetch current service alerts from MTA."""
    global _alerts_cache

    # Check cache
    if _alerts_cache:
        cached_alerts, cached_time = _alerts_cache
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return cached_alerts

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(ALERTS_FEED_URL, timeout=30.0)
            response.raise_for_status()

        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        alerts = _parse_alerts(feed)
        _alerts_cache = (alerts, time.time())
        return alerts

    except Exception:
        # Return cached data if available
        if _alerts_cache:
            return _alerts_cache[0]
        raise


def _parse_alerts(feed) -> list[ServiceAlert]:
    """Parse GTFS-RT alerts feed into our format."""
    alerts: list[ServiceAlert] = []
    now = time.time()

    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue

        alert = entity.alert

        # Extract affected routes and stops
        affected_lines: list[str] = []
        affected_stops: list[str] = []
        for informed in alert.informed_entity:
            if informed.route_id:
                affected_lines.append(informed.route_id)
            if informed.stop_id:
                affected_stops.append(informed.stop_id)

        # Extract active periods
        active_periods: list[dict] = []
        is_active = False
        for period in alert.active_period:
            start = datetime.fromtimestamp(period.start) if period.start else None
            end = datetime.fromtimestamp(period.end) if period.end else None
            active_periods.append({"start": start, "end": end})

            start_time = period.start or 0
            end_time = period.end or float("inf")
            if start_time <= now <= end_time:
                is_active = True

        if not active_periods:
            is_active = True

        header_text = _extract_text(alert.header_text)
        description_text = _extract_text(alert.description_text)

        alerts.append(ServiceAlert(
            id=entity.id,
            header_text=header_text,
            description_text=description_text,
            affected_lines=list(set(affected_lines)),
            affected_stops=list(set(affected_stops)),
            cause=CAUSE_MAP.get(alert.cause, "Unknown"),
            effect=EFFECT_MAP.get(alert.effect, "UNKNOWN_EFFECT"),
            active_periods=active_periods,
            is_active=is_active,
        ))

    # Filter to active alerts and sort by severity
    severity_order = ["NO_SERVICE", "SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR", "MODIFIED_SERVICE", "OTHER_EFFECT"]
    active_alerts = [a for a in alerts if a.is_active]
    return sorted(active_alerts, key=lambda a: severity_order.index(a.effect) if a.effect in severity_order else 99)


async def get_alerts_for_line(line: str) -> list[ServiceAlert]:
    """Get alerts for a specific line."""
    alerts = await fetch_service_alerts()
    return [a for a in alerts if line.upper() in a.affected_lines or not a.affected_lines]


async def get_alerts_for_lines(lines: list[str]) -> list[ServiceAlert]:
    """Get alerts for multiple lines."""
    alerts = await fetch_service_alerts()
    line_set = {l.upper() for l in lines}
    return [a for a in alerts if any(l in line_set for l in a.affected_lines) or not a.affected_lines]


async def get_all_alerts() -> list[ServiceAlert]:
    """Get all current service alerts."""
    return await fetch_service_alerts()


async def get_service_summary() -> dict:
    """Get a summary of current service status."""
    alerts = await fetch_service_alerts()

    all_lines = ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "B", "D", "F", "M", "N", "Q", "R", "W", "G", "J", "Z", "L", "S"]
    affected_lines: set[str] = set()
    suspended_lines: set[str] = set()
    delayed_lines: set[str] = set()

    for alert in alerts:
        for line in alert.affected_lines:
            affected_lines.add(line)
            if alert.effect == "NO_SERVICE":
                suspended_lines.add(line)
            elif alert.effect == "SIGNIFICANT_DELAYS":
                delayed_lines.add(line)

    good_service = [l for l in all_lines if l not in affected_lines]

    return {
        "good_service": good_service,
        "delays": list(delayed_lines),
        "suspended": list(suspended_lines),
        "alerts": alerts,
    }

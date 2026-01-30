"""GTFS-RT client for fetching real-time subway data."""
import logging
import time
from datetime import datetime
from typing import Literal, Optional

import httpx
from google.transit import gtfs_realtime_pb2

logger = logging.getLogger(__name__)

from ..data.types import FEED_URLS, LINE_TO_FEED, get_feed_url_for_line
from .types import ParsedArrival, ParsedFeed

# Cache with 30-second TTL
_feed_cache: dict[str, tuple[ParsedFeed, float]] = {}
CACHE_TTL_SECONDS = 30


async def fetch_feed(feed_url: str) -> ParsedFeed:
    """Fetch and parse a GTFS-RT feed."""
    # Check cache
    if feed_url in _feed_cache:
        cached_feed, cached_time = _feed_cache[feed_url]
        cache_age = time.time() - cached_time
        if cache_age < CACHE_TTL_SECONDS:
            logger.debug(f"[fetch_feed] Cache HIT for {feed_url} (age: {cache_age:.1f}s)")
            return cached_feed
        else:
            logger.debug(f"[fetch_feed] Cache EXPIRED for {feed_url} (age: {cache_age:.1f}s)")

    logger.debug(f"[fetch_feed] Fetching fresh feed from {feed_url}")

    # Fetch the protobuf data
    async with httpx.AsyncClient() as client:
        response = await client.get(feed_url, timeout=30.0)
        response.raise_for_status()

    # Parse protobuf
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    # Convert to our format
    parsed = _parse_feed(feed)
    logger.debug(f"[fetch_feed] Parsed {len(parsed.arrivals)} total arrivals from feed")

    # Cache the result
    _feed_cache[feed_url] = (parsed, time.time())

    return parsed


def _parse_feed(feed) -> ParsedFeed:
    """Parse a GTFS-RT FeedMessage into our format."""
    arrivals: list[ParsedArrival] = []
    now = time.time() * 1000  # milliseconds

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update
        trip = trip_update.trip

        route_id = trip.route_id or ""
        trip_id = trip.trip_id or entity.id

        # Determine direction from trip_id (NYCT encodes direction in trip_id)
        direction: Literal["N", "S"] = "N"
        if trip_id:
            # NYCT trip IDs often end with direction
            last_char = trip_id[-1] if trip_id else ""
            if last_char in ("N", "S"):
                direction = last_char  # type: ignore

        # Process each stop time update
        for stu in trip_update.stop_time_update:
            stop_id = stu.stop_id
            if not stop_id:
                continue

            # Determine direction from stop_id suffix (more reliable)
            stop_dir = stop_id[-1] if stop_id else ""
            if stop_dir in ("N", "S"):
                direction = stop_dir  # type: ignore

            # Get arrival time
            if not stu.HasField("arrival") or not stu.arrival.time:
                continue

            arrival_time = datetime.fromtimestamp(stu.arrival.time)

            # Skip arrivals in the past
            if arrival_time.timestamp() * 1000 < now - 60000:
                continue

            departure_time = None
            if stu.HasField("departure") and stu.departure.time:
                departure_time = datetime.fromtimestamp(stu.departure.time)

            arrivals.append(ParsedArrival(
                trip_id=trip_id,
                route_id=route_id,
                direction=direction,
                stop_id=stop_id,
                arrival_time=arrival_time,
                departure_time=departure_time,
                track=None,
                is_assigned=False,
            ))

    timestamp = datetime.fromtimestamp(feed.header.timestamp) if feed.header.timestamp else datetime.now()

    return ParsedFeed(timestamp=timestamp, arrivals=arrivals)


async def get_arrivals_for_line(line: str) -> list[ParsedArrival]:
    """Get arrivals for a specific line."""
    feed_url = get_feed_url_for_line(line)
    feed = await fetch_feed(feed_url)
    return [a for a in feed.arrivals if a.route_id == line.upper()]


async def get_arrivals_at_stop(
    line: str,
    stop_id: str,
    direction: Optional[Literal["N", "S"]] = None,
) -> list[ParsedArrival]:
    """Get arrivals at a specific stop for a line."""
    logger.debug(f"[get_arrivals_at_stop] Called with line={line}, stop_id={stop_id}, direction={direction}")

    feed_url = get_feed_url_for_line(line)
    feed = await fetch_feed(feed_url)

    base_stop_id = stop_id.rstrip("NS")
    logger.debug(f"[get_arrivals_at_stop] Looking for base_stop_id={base_stop_id} in {len(feed.arrivals)} arrivals")

    # Debug: count filtering stages
    route_matches = 0
    stop_matches = 0
    direction_matches = 0

    results = []
    for a in feed.arrivals:
        if a.route_id != line.upper():
            continue
        route_matches += 1

        arrival_base_stop = a.stop_id.rstrip("NS")
        if arrival_base_stop != base_stop_id:
            continue
        stop_matches += 1

        if direction and a.direction != direction:
            logger.debug(f"[get_arrivals_at_stop] FILTERED by direction: arrival.direction={a.direction}, wanted={direction}, arrival_time={a.arrival_time}")
            continue
        direction_matches += 1

        results.append(a)

    logger.debug(f"[get_arrivals_at_stop] Filtering stats: route_matches={route_matches}, stop_matches={stop_matches}, direction_matches={direction_matches}")
    logger.debug(f"[get_arrivals_at_stop] Returning {len(results)} arrivals")

    for i, r in enumerate(results[:5]):
        logger.debug(f"[get_arrivals_at_stop] Result[{i}]: line={r.route_id}, dir={r.direction}, stop={r.stop_id}, time={r.arrival_time}")

    return results


async def get_arrivals_at_stop_multi_line(
    lines: list[str],
    stop_id: str,
    direction: Optional[Literal["N", "S"]] = None,
) -> list[ParsedArrival]:
    """Get arrivals at a stop for multiple lines."""
    # Group lines by feed
    feed_groups: dict[str, list[str]] = {}
    for line in lines:
        feed_id = LINE_TO_FEED.get(line.upper())
        if not feed_id:
            continue
        if feed_id not in feed_groups:
            feed_groups[feed_id] = []
        feed_groups[feed_id].append(line.upper())

    # Fetch all needed feeds
    all_arrivals: list[ParsedArrival] = []
    base_stop_id = stop_id.rstrip("NS")
    line_set = {l.upper() for l in lines}

    for feed_id in feed_groups:
        feed = await fetch_feed(FEED_URLS[feed_id])
        for arrival in feed.arrivals:
            if arrival.route_id not in line_set:
                continue
            arrival_base_stop = arrival.stop_id.rstrip("NS")
            if arrival_base_stop != base_stop_id:
                continue
            if direction and arrival.direction != direction:
                continue
            all_arrivals.append(arrival)

    # Sort by arrival time
    return sorted(all_arrivals, key=lambda a: a.arrival_time)


def clear_cache() -> None:
    """Clear the feed cache."""
    _feed_cache.clear()

"""Time utilities for the subway agent."""
from datetime import datetime, timezone

# Eastern timezone offset (EST = UTC-5, EDT = UTC-4)
# Using a simple approach; for production, consider using pytz or zoneinfo
try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("America/New_York")
except ImportError:
    LOCAL_TZ = None


def to_local_time(dt: datetime) -> datetime:
    """Convert a datetime to local (Eastern) time."""
    if dt.tzinfo is None:
        # Assume naive datetimes from GTFS are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    if LOCAL_TZ:
        return dt.astimezone(LOCAL_TZ)
    else:
        # Fallback: manual EST offset (doesn't handle DST)
        from datetime import timedelta
        return dt.astimezone(timezone(timedelta(hours=-5)))


def format_minutes_away(arrival_time: datetime) -> str:
    """Format minutes until arrival."""
    diff_minutes = get_minutes_away(arrival_time)
    if diff_minutes <= 0:
        return "arriving now"
    elif diff_minutes == 1:
        return "1 min"
    else:
        return f"{diff_minutes} mins"


def get_minutes_away(arrival_time: datetime) -> int:
    """Get minutes until arrival as a number."""
    now = datetime.now(timezone.utc)
    if arrival_time.tzinfo is None:
        # Assume naive datetimes from GTFS are UTC
        arrival_time = arrival_time.replace(tzinfo=timezone.utc)
    diff_seconds = (arrival_time - now).total_seconds()
    return round(diff_seconds / 60)


def format_time(dt: datetime) -> str:
    """Format time as HH:MM AM/PM in local timezone."""
    local_dt = to_local_time(dt)
    return local_dt.strftime("%-I:%M %p")


def format_time_24(dt: datetime) -> str:
    """Format time as HH:MM (24-hour) in local timezone."""
    local_dt = to_local_time(dt)
    return local_dt.strftime("%H:%M")


def describe_wait(minutes: int) -> str:
    """Get a human-readable description of the wait time."""
    if minutes <= 0:
        return "no wait"
    elif minutes == 1:
        return "1 minute wait"
    elif minutes < 60:
        return f"{minutes} minute wait"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return "1 hour wait" if hours == 1 else f"{hours} hour wait"
        return f"{hours}h {mins}m wait"


def is_within_window(dt: datetime, window_minutes: int) -> bool:
    """Check if a datetime is within a time window from now."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff_seconds = (dt - now).total_seconds()
    minutes = round(diff_seconds / 60)
    return 0 <= minutes <= window_minutes


def get_minutes_diff(later: datetime, earlier: datetime) -> float:
    """Get the difference in minutes between two datetimes."""
    # Ensure both are timezone-aware for proper comparison
    if later.tzinfo is None:
        later = later.replace(tzinfo=timezone.utc)
    if earlier.tzinfo is None:
        earlier = earlier.replace(tzinfo=timezone.utc)
    return (later - earlier).total_seconds() / 60

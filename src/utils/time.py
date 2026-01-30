"""Time utilities for the subway agent."""
from datetime import datetime


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
    now = datetime.now()
    diff_seconds = (arrival_time - now).total_seconds()
    return round(diff_seconds / 60)


def format_time(dt: datetime) -> str:
    """Format time as HH:MM AM/PM."""
    return dt.strftime("%-I:%M %p")


def format_time_24(dt: datetime) -> str:
    """Format time as HH:MM (24-hour)."""
    return dt.strftime("%H:%M")


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
    """Check if a date is within a time window from now."""
    minutes = get_minutes_away(dt)
    return 0 <= minutes <= window_minutes


def get_minutes_diff(later: datetime, earlier: datetime) -> float:
    """Get the difference in minutes between two dates."""
    return (later - earlier).total_seconds() / 60

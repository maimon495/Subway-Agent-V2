"""Cross-platform transfer stations for local-to-express optimization."""
from typing import Optional
from .types import TransferPoint

TRANSFER_POINTS: list[TransferPoint] = [
    # === IRT LEXINGTON AVENUE LINE (4/5/6) ===
    TransferPoint("14th-st-union-sq", "14th St - Union Square", {"express": ["4", "5"], "local": ["6"]}, True, 0, "Cross-platform transfer on same level"),
    TransferPoint("42nd-st-grand-central", "Grand Central - 42nd St", {"express": ["4", "5"], "local": ["6"]}, True, 0, "Cross-platform transfer on same level"),
    TransferPoint("brooklyn-bridge", "Brooklyn Bridge - City Hall", {"express": ["4", "5"], "local": ["6"]}, True, 0, "Cross-platform, last express stop going downtown"),
    TransferPoint("59th-st-lex", "59th St", {"express": ["4", "5"], "local": ["6"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("86th-st-lex", "86th St", {"express": ["4", "5"], "local": ["6"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("125th-st-lex", "125th St", {"express": ["4", "5"], "local": ["6"]}, True, 0, "Cross-platform transfer"),
    # === IRT BROADWAY-SEVENTH AVENUE LINE (1/2/3) ===
    TransferPoint("14th-st-7av", "14th St", {"express": ["2", "3"], "local": ["1"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("34th-st-penn", "34th St - Penn Station", {"express": ["2", "3"], "local": ["1"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("42nd-st-times-sq", "Times Sq - 42nd St", {"express": ["2", "3"], "local": ["1"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("72nd-st-bway", "72nd St", {"express": ["2", "3"], "local": ["1"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("96th-st-bway", "96th St", {"express": ["2", "3"], "local": ["1"]}, True, 0, "Cross-platform transfer, last express stop going uptown"),
    TransferPoint("chambers-st-1", "Chambers St", {"express": ["2", "3"], "local": ["1"]}, True, 0, "Cross-platform transfer, last express stop going downtown"),
    # === BMT BROADWAY LINE (N/Q/R/W) ===
    TransferPoint("14th-st-union-sq", "14th St - Union Square", {"express": ["N", "Q"], "local": ["R", "W"]}, True, 0, "Cross-platform transfer for Broadway line"),
    TransferPoint("34th-st-herald-sq", "34th St - Herald Square", {"express": ["N", "Q"], "local": ["R", "W"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("42nd-st-times-sq", "Times Sq - 42nd St", {"express": ["N", "Q"], "local": ["R", "W"]}, True, 0, "Cross-platform transfer for Broadway line"),
    TransferPoint("canal-st-nqrw", "Canal St", {"express": ["N", "Q"], "local": ["R", "W"]}, True, 0, "Cross-platform transfer, key downtown station"),
    TransferPoint("57th-st-7av", "57th St - 7th Ave", {"express": ["N", "Q"], "local": ["R", "W"]}, True, 0, "Cross-platform transfer"),
    # === IND EIGHTH AVENUE LINE (A/C/E) ===
    TransferPoint("14th-st-8av", "14th St", {"express": ["A"], "local": ["C", "E"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("34th-st-pabt", "34th St - Penn Station", {"express": ["A"], "local": ["C", "E"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("42nd-st-pabt", "42nd St - Port Authority", {"express": ["A"], "local": ["C", "E"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("59th-st-columbus-ace", "59th St - Columbus Circle", {"express": ["A"], "local": ["C"]}, True, 0, "Cross-platform transfer, E doesn't stop here"),
    TransferPoint("canal-st-ace", "Canal St", {"express": ["A"], "local": ["C", "E"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("chambers-st-ace", "Chambers St", {"express": ["A"], "local": ["C"]}, True, 0, "Cross-platform transfer, E goes to WTC"),
    # === IND SIXTH AVENUE LINE (B/D/F/M) ===
    TransferPoint("34th-st-herald-sq", "34th St - Herald Square", {"express": ["B", "D"], "local": ["F", "M"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("42nd-st-bryant-park", "42nd St - Bryant Park", {"express": ["B", "D"], "local": ["F", "M"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("47-50-sts-rock", "47-50 Sts - Rockefeller Center", {"express": ["B", "D"], "local": ["F", "M"]}, True, 0, "Cross-platform transfer"),
    TransferPoint("west-4th-st", "West 4th St - Washington Sq", {"express": ["B", "D"], "local": ["F", "M"]}, True, 0, "Cross-platform transfer at mezzanine level"),
    TransferPoint("broadway-lafayette", "Broadway - Lafayette St", {"express": ["B", "D"], "local": ["F", "M"]}, True, 0, "Cross-platform transfer"),
]

# Build lookup maps
_transfers_by_station: dict[str, list[TransferPoint]] = {}
for tp in TRANSFER_POINTS:
    if tp.station_id not in _transfers_by_station:
        _transfers_by_station[tp.station_id] = []
    _transfers_by_station[tp.station_id].append(tp)

_transfers_by_line: dict[str, list[TransferPoint]] = {}
for tp in TRANSFER_POINTS:
    for line in tp.lines["express"] + tp.lines["local"]:
        if line not in _transfers_by_line:
            _transfers_by_line[line] = []
        if not any(e.station_id == tp.station_id for e in _transfers_by_line[line]):
            _transfers_by_line[line].append(tp)


def get_transfer_points_for_station(station_id: str) -> list[TransferPoint]:
    """Get transfer points at a station."""
    return _transfers_by_station.get(station_id, [])


def get_transfer_points_for_line(line_id: str) -> list[TransferPoint]:
    """Get transfer points on a line."""
    return _transfers_by_line.get(line_id.upper(), [])


def find_transfer_point(station_id: str, local_line: str, express_line: str) -> Optional[TransferPoint]:
    """Find a specific transfer point."""
    transfers = _transfers_by_station.get(station_id, [])
    for tp in transfers:
        if local_line.upper() in tp.lines["local"] and express_line.upper() in tp.lines["express"]:
            return tp
    return None


def get_transfer_points_between(local_line: str, express_line: str) -> list[TransferPoint]:
    """Get all transfer points between a local and express line."""
    return [
        tp for tp in TRANSFER_POINTS
        if local_line.upper() in tp.lines["local"] and express_line.upper() in tp.lines["express"]
    ]

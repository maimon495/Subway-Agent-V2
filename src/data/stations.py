"""NYC Subway station database."""
from typing import Optional
from .types import Station

STATIONS: list[Station] = [
    # === IRT LEXINGTON AVENUE LINE (4/5/6) ===
    Station(
        id="south-ferry",
        name="South Ferry",
        aliases=["south ferry", "whitehall", "staten island ferry"],
        gtfs_stop_ids={"N": "142N", "S": "142S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="bowling-green",
        name="Bowling Green",
        aliases=["bowling green"],
        gtfs_stop_ids={"N": "419N", "S": "419S"},
        lines=["4", "5"],
        is_express={"4": True, "5": True},
        borough="Manhattan",
    ),
    Station(
        id="wall-st-lex",
        name="Wall St",
        aliases=["wall street", "wall st 4 5"],
        gtfs_stop_ids={"N": "418N", "S": "418S"},
        lines=["4", "5"],
        is_express={"4": True, "5": True},
        borough="Manhattan",
    ),
    Station(
        id="fulton-st",
        name="Fulton St",
        aliases=["fulton street", "fulton", "broadway-nassau"],
        gtfs_stop_ids={"N": "A38N", "S": "A38S"},
        lines=["2", "3", "4", "5", "A", "C", "J", "Z"],
        is_express={"2": True, "3": True, "4": True, "5": True, "A": True, "C": False, "J": False, "Z": True},
        borough="Manhattan",
        complex_id="fulton-complex",
    ),
    Station(
        id="brooklyn-bridge",
        name="Brooklyn Bridge - City Hall",
        aliases=["brooklyn bridge", "city hall", "chambers 4 5 6"],
        gtfs_stop_ids={"N": "417N", "S": "417S"},
        lines=["4", "5", "6"],
        is_express={"4": True, "5": True, "6": False},
        borough="Manhattan",
    ),
    Station(
        id="14th-st-union-sq",
        name="14th St - Union Square",
        aliases=["union square", "union sq", "14th street union square", "14 st union sq"],
        gtfs_stop_ids={"N": "635N", "S": "635S"},
        lines=["4", "5", "6", "N", "Q", "R", "W", "L"],
        is_express={"4": True, "5": True, "6": False, "N": True, "Q": True, "R": False, "W": False, "L": False},
        borough="Manhattan",
        complex_id="union-square",
    ),
    Station(
        id="23rd-st-lex",
        name="23rd St",
        aliases=["23rd street", "23 st 6"],
        gtfs_stop_ids={"N": "626N", "S": "626S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="28th-st-lex",
        name="28th St",
        aliases=["28th street", "28 st 6"],
        gtfs_stop_ids={"N": "625N", "S": "625S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="33rd-st-lex",
        name="33rd St",
        aliases=["33rd street", "33 st 6"],
        gtfs_stop_ids={"N": "624N", "S": "624S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="42nd-st-grand-central",
        name="Grand Central - 42nd St",
        aliases=["grand central", "42nd street grand central", "gct", "42 st 4 5 6", "grand central terminal"],
        gtfs_stop_ids={"N": "631N", "S": "631S"},
        lines=["4", "5", "6", "7", "S"],
        is_express={"4": True, "5": True, "6": False, "7": False, "S": False},
        borough="Manhattan",
        complex_id="grand-central",
    ),
    Station(
        id="51st-st",
        name="51st St",
        aliases=["51st street", "51 st 6"],
        gtfs_stop_ids={"N": "622N", "S": "622S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="59th-st-lex",
        name="59th St",
        aliases=["59th street lex", "59 st 4 5 6", "bloomingdales"],
        gtfs_stop_ids={"N": "621N", "S": "621S"},
        lines=["4", "5", "6"],
        is_express={"4": True, "5": True, "6": False},
        borough="Manhattan",
    ),
    Station(
        id="68th-st",
        name="68th St - Hunter College",
        aliases=["68th street", "hunter college", "68 st 6"],
        gtfs_stop_ids={"N": "620N", "S": "620S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="77th-st",
        name="77th St",
        aliases=["77th street", "77 st 6"],
        gtfs_stop_ids={"N": "619N", "S": "619S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="86th-st-lex",
        name="86th St",
        aliases=["86th street lex", "86 st 4 5 6"],
        gtfs_stop_ids={"N": "618N", "S": "618S"},
        lines=["4", "5", "6"],
        is_express={"4": True, "5": True, "6": False},
        borough="Manhattan",
    ),
    Station(
        id="96th-st-lex",
        name="96th St",
        aliases=["96th street lex", "96 st 6"],
        gtfs_stop_ids={"N": "617N", "S": "617S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="103rd-st-lex",
        name="103rd St",
        aliases=["103rd street lex", "103 st 6"],
        gtfs_stop_ids={"N": "616N", "S": "616S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="110th-st-lex",
        name="110th St",
        aliases=["110th street lex", "110 st 6"],
        gtfs_stop_ids={"N": "615N", "S": "615S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="116th-st-lex",
        name="116th St",
        aliases=["116th street lex", "116 st 6"],
        gtfs_stop_ids={"N": "614N", "S": "614S"},
        lines=["6"],
        is_express={"6": False},
        borough="Manhattan",
    ),
    Station(
        id="125th-st-lex",
        name="125th St",
        aliases=["125th street lex", "125 st 4 5 6", "harlem 125"],
        gtfs_stop_ids={"N": "621N", "S": "621S"},
        lines=["4", "5", "6"],
        is_express={"4": True, "5": True, "6": False},
        borough="Manhattan",
    ),
    # === IRT BROADWAY-SEVENTH AVENUE LINE (1/2/3) ===
    Station(
        id="chambers-st-1",
        name="Chambers St",
        aliases=["chambers street", "chambers 1 2 3"],
        gtfs_stop_ids={"N": "137N", "S": "137S"},
        lines=["1", "2", "3"],
        is_express={"1": False, "2": True, "3": True},
        borough="Manhattan",
    ),
    Station(
        id="14th-st-7av",
        name="14th St",
        aliases=["14th street 7th ave", "14 st 1 2 3"],
        gtfs_stop_ids={"N": "132N", "S": "132S"},
        lines=["1", "2", "3"],
        is_express={"1": False, "2": True, "3": True},
        borough="Manhattan",
    ),
    Station(
        id="18th-st-1",
        name="18th St",
        aliases=["18th street", "18 st 1"],
        gtfs_stop_ids={"N": "131N", "S": "131S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="23rd-st-1",
        name="23rd St",
        aliases=["23rd street 1", "23 st 1"],
        gtfs_stop_ids={"N": "130N", "S": "130S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="28th-st-1",
        name="28th St",
        aliases=["28th street 1", "28 st 1"],
        gtfs_stop_ids={"N": "129N", "S": "129S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="34th-st-penn",
        name="34th St - Penn Station",
        aliases=["penn station", "34th street penn", "34 st 1 2 3", "penn sta", "madison square garden", "msg"],
        gtfs_stop_ids={"N": "128N", "S": "128S"},
        lines=["1", "2", "3"],
        is_express={"1": False, "2": True, "3": True},
        borough="Manhattan",
        complex_id="penn-station",
    ),
    Station(
        id="42nd-st-times-sq",
        name="Times Sq - 42nd St",
        aliases=["times square", "42nd street times square", "times sq", "42 st 1 2 3", "port authority"],
        gtfs_stop_ids={"N": "127N", "S": "127S"},
        lines=["1", "2", "3", "7", "N", "Q", "R", "W", "S"],
        is_express={"1": False, "2": True, "3": True, "7": False, "N": True, "Q": True, "R": False, "W": False, "S": False},
        borough="Manhattan",
        complex_id="times-square",
    ),
    Station(
        id="50th-st-1",
        name="50th St",
        aliases=["50th street 1", "50 st 1"],
        gtfs_stop_ids={"N": "126N", "S": "126S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="59th-st-columbus",
        name="59th St - Columbus Circle",
        aliases=["columbus circle", "59th street columbus", "59 st 1"],
        gtfs_stop_ids={"N": "125N", "S": "125S"},
        lines=["1", "A", "C", "B", "D"],
        is_express={"1": False, "A": True, "C": False, "B": True, "D": True},
        borough="Manhattan",
        complex_id="columbus-circle",
    ),
    Station(
        id="66th-st-lincoln",
        name="66th St - Lincoln Center",
        aliases=["lincoln center", "66th street", "66 st 1"],
        gtfs_stop_ids={"N": "124N", "S": "124S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="72nd-st-bway",
        name="72nd St",
        aliases=["72nd street broadway", "72 st 1 2 3"],
        gtfs_stop_ids={"N": "123N", "S": "123S"},
        lines=["1", "2", "3"],
        is_express={"1": False, "2": True, "3": True},
        borough="Manhattan",
    ),
    Station(
        id="79th-st-1",
        name="79th St",
        aliases=["79th street", "79 st 1"],
        gtfs_stop_ids={"N": "122N", "S": "122S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="86th-st-bway",
        name="86th St",
        aliases=["86th street broadway", "86 st 1"],
        gtfs_stop_ids={"N": "121N", "S": "121S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="96th-st-bway",
        name="96th St",
        aliases=["96th street broadway", "96 st 1 2 3"],
        gtfs_stop_ids={"N": "120N", "S": "120S"},
        lines=["1", "2", "3"],
        is_express={"1": False, "2": True, "3": True},
        borough="Manhattan",
    ),
    Station(
        id="103rd-st-1",
        name="103rd St",
        aliases=["103rd street 1", "103 st 1"],
        gtfs_stop_ids={"N": "119N", "S": "119S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="110th-st-cathedral",
        name="Cathedral Pkwy - 110th St",
        aliases=["cathedral parkway", "110th street 1", "110 st 1"],
        gtfs_stop_ids={"N": "118N", "S": "118S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    Station(
        id="116th-st-columbia",
        name="116th St - Columbia University",
        aliases=["columbia university", "columbia", "116th street 1", "116 st 1"],
        gtfs_stop_ids={"N": "117N", "S": "117S"},
        lines=["1"],
        is_express={"1": False},
        borough="Manhattan",
    ),
    # === BMT BROADWAY LINE (N/Q/R/W) ===
    Station(
        id="city-hall-nrw",
        name="City Hall",
        aliases=["city hall r w", "city hall nrw"],
        gtfs_stop_ids={"N": "R25N", "S": "R25S"},
        lines=["R", "W"],
        is_express={"R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="canal-st-nqrw",
        name="Canal St",
        aliases=["canal street nqrw", "canal st broadway"],
        gtfs_stop_ids={"N": "R23N", "S": "R23S"},
        lines=["N", "Q", "R", "W"],
        is_express={"N": True, "Q": True, "R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="prince-st",
        name="Prince St",
        aliases=["prince street", "prince st r w", "soho"],
        gtfs_stop_ids={"N": "R22N", "S": "R22S"},
        lines=["R", "W"],
        is_express={"R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="8th-st-nyu",
        name="8th St - NYU",
        aliases=["8th street nyu", "nyu", "astor place area", "8 st r w"],
        gtfs_stop_ids={"N": "R21N", "S": "R21S"},
        lines=["R", "W"],
        is_express={"R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="23rd-st-nrw",
        name="23rd St",
        aliases=["23rd street nrw", "23 st r w"],
        gtfs_stop_ids={"N": "R19N", "S": "R19S"},
        lines=["R", "W"],
        is_express={"R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="28th-st-nrw",
        name="28th St",
        aliases=["28th street nrw", "28 st r w"],
        gtfs_stop_ids={"N": "R18N", "S": "R18S"},
        lines=["R", "W"],
        is_express={"R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="34th-st-herald-sq",
        name="34th St - Herald Square",
        aliases=["herald square", "34th street herald", "macys", "34 st nqrw bdfm"],
        gtfs_stop_ids={"N": "R17N", "S": "R17S"},
        lines=["N", "Q", "R", "W", "B", "D", "F", "M"],
        is_express={"N": True, "Q": True, "R": False, "W": False, "B": True, "D": True, "F": False, "M": False},
        borough="Manhattan",
        complex_id="herald-square",
    ),
    Station(
        id="42nd-st-bryant-park",
        name="42nd St - Bryant Park",
        aliases=["bryant park", "42nd street bryant park", "42 st bdfm"],
        gtfs_stop_ids={"N": "D14N", "S": "D14S"},
        lines=["B", "D", "F", "M"],
        is_express={"B": True, "D": True, "F": False, "M": False},
        borough="Manhattan",
    ),
    Station(
        id="49th-st",
        name="49th St",
        aliases=["49th street", "49 st n r w", "rockefeller center area"],
        gtfs_stop_ids={"N": "R15N", "S": "R15S"},
        lines=["N", "R", "W"],
        is_express={"N": True, "R": False, "W": False},
        borough="Manhattan",
    ),
    Station(
        id="57th-st-7av",
        name="57th St - 7th Ave",
        aliases=["57th street 7th ave", "57 st n q r w", "carnegie hall"],
        gtfs_stop_ids={"N": "R14N", "S": "R14S"},
        lines=["N", "Q", "R", "W"],
        is_express={"N": True, "Q": True, "R": False, "W": False},
        borough="Manhattan",
    ),
    # === IND EIGHTH AVENUE LINE (A/C/E) ===
    Station(
        id="world-trade-center",
        name="World Trade Center",
        aliases=["wtc", "world trade", "cortlandt st e"],
        gtfs_stop_ids={"N": "E01N", "S": "E01S"},
        lines=["E"],
        is_express={"E": False},
        borough="Manhattan",
    ),
    Station(
        id="chambers-st-ace",
        name="Chambers St",
        aliases=["chambers street ace", "chambers a c e"],
        gtfs_stop_ids={"N": "A32N", "S": "A32S"},
        lines=["A", "C"],
        is_express={"A": True, "C": False},
        borough="Manhattan",
    ),
    Station(
        id="canal-st-ace",
        name="Canal St",
        aliases=["canal street ace", "canal st a c e"],
        gtfs_stop_ids={"N": "A34N", "S": "A34S"},
        lines=["A", "C", "E"],
        is_express={"A": True, "C": False, "E": False},
        borough="Manhattan",
    ),
    Station(
        id="spring-st-ace",
        name="Spring St",
        aliases=["spring street", "spring st c e"],
        gtfs_stop_ids={"N": "A33N", "S": "A33S"},
        lines=["C", "E"],
        is_express={"C": False, "E": False},
        borough="Manhattan",
    ),
    Station(
        id="west-4th-st",
        name="West 4th St - Washington Sq",
        aliases=["west 4th street", "washington square", "w 4 st", "west fourth"],
        gtfs_stop_ids={"N": "A31N", "S": "A31S"},
        lines=["A", "C", "E", "B", "D", "F", "M"],
        is_express={"A": True, "C": False, "E": False, "B": True, "D": True, "F": False, "M": False},
        borough="Manhattan",
        complex_id="west-4th",
    ),
    Station(
        id="14th-st-8av",
        name="14th St",
        aliases=["14th street 8th ave", "14 st a c e"],
        gtfs_stop_ids={"N": "A31N", "S": "A31S"},
        lines=["A", "C", "E"],
        is_express={"A": True, "C": False, "E": False},
        borough="Manhattan",
    ),
    Station(
        id="23rd-st-8av",
        name="23rd St",
        aliases=["23rd street 8th ave", "23 st c e"],
        gtfs_stop_ids={"N": "A28N", "S": "A28S"},
        lines=["C", "E"],
        is_express={"C": False, "E": False},
        borough="Manhattan",
    ),
    Station(
        id="34th-st-pabt",
        name="34th St - Penn Station",
        aliases=["34th street penn ace", "port authority", "34 st a c e"],
        gtfs_stop_ids={"N": "A27N", "S": "A27S"},
        lines=["A", "C", "E"],
        is_express={"A": True, "C": False, "E": False},
        borough="Manhattan",
        complex_id="penn-station",
    ),
    Station(
        id="42nd-st-pabt",
        name="42nd St - Port Authority",
        aliases=["port authority bus terminal", "42nd street port authority", "42 st a c e", "pabt"],
        gtfs_stop_ids={"N": "A27N", "S": "A27S"},
        lines=["A", "C", "E"],
        is_express={"A": True, "C": False, "E": False},
        borough="Manhattan",
    ),
    Station(
        id="50th-st-ace",
        name="50th St",
        aliases=["50th street ace", "50 st c e"],
        gtfs_stop_ids={"N": "A25N", "S": "A25S"},
        lines=["C", "E"],
        is_express={"C": False, "E": False},
        borough="Manhattan",
    ),
    Station(
        id="59th-st-columbus-ace",
        name="59th St - Columbus Circle",
        aliases=["columbus circle ace", "59 st a c b d"],
        gtfs_stop_ids={"N": "A24N", "S": "A24S"},
        lines=["A", "C", "B", "D"],
        is_express={"A": True, "C": False, "B": True, "D": True},
        borough="Manhattan",
        complex_id="columbus-circle",
    ),
    # === IND SIXTH AVENUE LINE (B/D/F/M) ===
    Station(
        id="broadway-lafayette",
        name="Broadway - Lafayette St",
        aliases=["broadway lafayette", "bleecker st", "bway lafayette"],
        gtfs_stop_ids={"N": "D21N", "S": "D21S"},
        lines=["B", "D", "F", "M"],
        is_express={"B": True, "D": True, "F": False, "M": False},
        borough="Manhattan",
    ),
    Station(
        id="14th-st-6av",
        name="14th St",
        aliases=["14th street 6th ave", "14 st f m"],
        gtfs_stop_ids={"N": "D18N", "S": "D18S"},
        lines=["F", "M"],
        is_express={"F": False, "M": False},
        borough="Manhattan",
    ),
    Station(
        id="23rd-st-6av",
        name="23rd St",
        aliases=["23rd street 6th ave", "23 st f m"],
        gtfs_stop_ids={"N": "D17N", "S": "D17S"},
        lines=["F", "M"],
        is_express={"F": False, "M": False},
        borough="Manhattan",
    ),
    Station(
        id="47-50-sts-rock",
        name="47-50 Sts - Rockefeller Center",
        aliases=["rockefeller center", "rock center", "47-50 streets", "47 50 sts"],
        gtfs_stop_ids={"N": "D15N", "S": "D15S"},
        lines=["B", "D", "F", "M"],
        is_express={"B": True, "D": True, "F": False, "M": False},
        borough="Manhattan",
    ),
    # === L TRAIN ===
    Station(
        id="14th-st-8av-l",
        name="8th Ave",
        aliases=["8th avenue l", "14th st 8th ave l", "8 av l"],
        gtfs_stop_ids={"N": "L01N", "S": "L01S"},
        lines=["L"],
        is_express={"L": False},
        borough="Manhattan",
    ),
    Station(
        id="6th-av-l",
        name="6th Ave",
        aliases=["6th avenue l", "14th st 6th ave l", "6 av l"],
        gtfs_stop_ids={"N": "L02N", "S": "L02S"},
        lines=["L"],
        is_express={"L": False},
        borough="Manhattan",
    ),
    Station(
        id="14th-st-union-sq-l",
        name="Union Sq - 14th St",
        aliases=["union square l", "14 st l"],
        gtfs_stop_ids={"N": "L03N", "S": "L03S"},
        lines=["L"],
        is_express={"L": False},
        borough="Manhattan",
        complex_id="union-square",
    ),
    Station(
        id="3rd-av-l",
        name="3rd Ave",
        aliases=["3rd avenue l", "third ave l", "3 av l"],
        gtfs_stop_ids={"N": "L05N", "S": "L05S"},
        lines=["L"],
        is_express={"L": False},
        borough="Manhattan",
    ),
    Station(
        id="1st-av-l",
        name="1st Ave",
        aliases=["1st avenue l", "first ave l", "1 av l"],
        gtfs_stop_ids={"N": "L06N", "S": "L06S"},
        lines=["L"],
        is_express={"L": False},
        borough="Manhattan",
    ),
    # === 7 TRAIN ===
    Station(
        id="34th-st-hudson-yards",
        name="34th St - Hudson Yards",
        aliases=["hudson yards", "34 st 7"],
        gtfs_stop_ids={"N": "726N", "S": "726S"},
        lines=["7"],
        is_express={"7": False},
        borough="Manhattan",
    ),
]

# Build lookup maps
_station_by_id: dict[str, Station] = {s.id: s for s in STATIONS}

_station_by_gtfs_id: dict[str, Station] = {}
for station in STATIONS:
    base_id = station.gtfs_stop_ids["N"].rstrip("N")
    _station_by_gtfs_id[base_id] = station
    _station_by_gtfs_id[station.gtfs_stop_ids["N"]] = station
    _station_by_gtfs_id[station.gtfs_stop_ids["S"]] = station

_stations_by_line: dict[str, list[Station]] = {}
for station in STATIONS:
    for line in station.lines:
        if line not in _stations_by_line:
            _stations_by_line[line] = []
        _stations_by_line[line].append(station)


def get_station_by_id(station_id: str) -> Optional[Station]:
    """Get a station by its internal ID."""
    return _station_by_id.get(station_id)


def get_station_by_gtfs_id(gtfs_id: str) -> Optional[Station]:
    """Get a station by its GTFS stop ID."""
    base_id = gtfs_id.rstrip("NS")
    return _station_by_gtfs_id.get(base_id) or _station_by_gtfs_id.get(gtfs_id)


def get_stations_for_line(line_id: str) -> list[Station]:
    """Get all stations on a given line."""
    return _stations_by_line.get(line_id.upper(), [])


def find_station_by_name(query: str) -> Optional[Station]:
    """Find a station by name or alias."""
    normalized = query.lower().strip()

    # Direct ID match
    if normalized in _station_by_id:
        return _station_by_id[normalized]

    # Exact name match
    for station in STATIONS:
        if station.name.lower() == normalized:
            return station

    # Alias match
    for station in STATIONS:
        if any(alias.lower() == normalized for alias in station.aliases):
            return station

    # Partial match - station name contains query
    for station in STATIONS:
        if normalized in station.name.lower():
            return station

    # Partial match - query in aliases
    for station in STATIONS:
        if any(normalized in alias.lower() for alias in station.aliases):
            return station

    return None


def find_stations_by_name(query: str, limit: int = 5) -> list[Station]:
    """Find stations matching a query, returning up to limit results."""
    normalized = query.lower().strip()
    results: list[Station] = []
    seen: set[str] = set()

    # Exact matches first
    for station in STATIONS:
        if station.name.lower() == normalized or any(a.lower() == normalized for a in station.aliases):
            if station.id not in seen:
                results.append(station)
                seen.add(station.id)

    # Partial matches
    if len(results) < limit:
        for station in STATIONS:
            if station.id in seen:
                continue
            if normalized in station.name.lower() or any(normalized in a.lower() for a in station.aliases):
                results.append(station)
                seen.add(station.id)
                if len(results) >= limit:
                    break

    return results

"""NYC Subway line configurations."""
from typing import Optional
from .types import SubwayLine

LINES: list[SubwayLine] = [
    # IRT Lines (numbered)
    SubwayLine("1", "Broadway-Seventh Avenue Local", "#EE352E", "123456S", "local", "IRT"),
    SubwayLine("2", "Seventh Avenue Express", "#EE352E", "123456S", "express", "IRT"),
    SubwayLine("3", "Seventh Avenue Express", "#EE352E", "123456S", "express", "IRT"),
    SubwayLine("4", "Lexington Avenue Express", "#00933C", "123456S", "express", "IRT"),
    SubwayLine("5", "Lexington Avenue Express", "#00933C", "123456S", "express", "IRT"),
    SubwayLine("6", "Lexington Avenue Local", "#00933C", "123456S", "local", "IRT"),
    SubwayLine("7", "Flushing Local/Express", "#B933AD", "7", "mixed", "IRT"),
    # IND Lines
    SubwayLine("A", "Eighth Avenue Express", "#0039A6", "ACE", "express", "IND"),
    SubwayLine("C", "Eighth Avenue Local", "#0039A6", "ACE", "local", "IND"),
    SubwayLine("E", "Eighth Avenue Local", "#0039A6", "ACE", "local", "IND"),
    SubwayLine("B", "Sixth Avenue Express", "#FF6319", "BDFM", "express", "IND"),
    SubwayLine("D", "Sixth Avenue Express", "#FF6319", "BDFM", "express", "IND"),
    SubwayLine("F", "Sixth Avenue Local", "#FF6319", "BDFM", "local", "IND"),
    SubwayLine("M", "Sixth Avenue Local", "#FF6319", "BDFM", "local", "IND"),
    SubwayLine("G", "Brooklyn-Queens Crosstown", "#6CBE45", "G", "local", "IND"),
    # BMT Lines
    SubwayLine("J", "Nassau Street Local", "#996633", "JZ", "local", "BMT"),
    SubwayLine("Z", "Nassau Street Express", "#996633", "JZ", "express", "BMT"),
    SubwayLine("L", "Canarsie", "#A7A9AC", "L", "local", "BMT"),
    SubwayLine("N", "Broadway Express", "#FCCC0A", "NQRW", "express", "BMT"),
    SubwayLine("Q", "Broadway Express", "#FCCC0A", "NQRW", "express", "BMT"),
    SubwayLine("R", "Broadway Local", "#FCCC0A", "NQRW", "local", "BMT"),
    SubwayLine("W", "Broadway Local", "#FCCC0A", "NQRW", "local", "BMT"),
    # Shuttles
    SubwayLine("S", "42nd Street Shuttle", "#808183", "123456S", "local", "IRT"),
]

LINE_MAP: dict[str, SubwayLine] = {line.id: line for line in LINES}


def get_line(line_id: str) -> Optional[SubwayLine]:
    """Get a subway line by its ID."""
    return LINE_MAP.get(line_id.upper())


def is_express_line(line_id: str) -> bool:
    """Check if a line is an express line."""
    line = get_line(line_id)
    return line.type == "express" if line else False


def get_line_color(line_id: str) -> str:
    """Get the color code for a line."""
    line = get_line(line_id)
    return line.color if line else "#808183"


# Express-local pairs for same trunk line
EXPRESS_LOCAL_PAIRS: dict[str, dict[str, list[str]]] = {
    "lex": {"express": ["4", "5"], "local": ["6"]},
    "broadway-7av": {"express": ["2", "3"], "local": ["1"]},
    "broadway-bmt": {"express": ["N", "Q"], "local": ["R", "W"]},
    "8av": {"express": ["A"], "local": ["C", "E"]},
    "6av": {"express": ["B", "D"], "local": ["F", "M"]},
}


def get_trunk_line(line_id: str) -> Optional[str]:
    """Get the trunk line for express/local pairing."""
    line = line_id.upper()
    if line in ["4", "5", "6"]:
        return "lex"
    if line in ["1", "2", "3"]:
        return "broadway-7av"
    if line in ["N", "Q", "R", "W"]:
        return "broadway-bmt"
    if line in ["A", "C", "E"]:
        return "8av"
    if line in ["B", "D", "F", "M"]:
        return "6av"
    return None


def get_express_alternative(local_line: str) -> list[str]:
    """Get the express alternative for a local line."""
    trunk = get_trunk_line(local_line)
    if not trunk:
        return []
    pair = EXPRESS_LOCAL_PAIRS.get(trunk)
    if not pair or local_line.upper() not in pair["local"]:
        return []
    return pair["express"]

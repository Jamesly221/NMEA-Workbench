"""Inspect ordinary NMEA 0183 sentences; do not treat checksums as sensor validity."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
import math
import re


@dataclass
class Message:
    raw: str
    talker: str = ""
    kind: str = ""
    values: list[str] = field(default_factory=list)
    checksum: str = "Unavailable"
    expected: str = ""
    supplied: str = ""
    issues: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)

    @property
    def health(self):
        if self.issues:
            return "Review"
        if self.checksum == "Valid":
            return "OK"
        return self.checksum


def checksum(body):
    result = 0
    for character in body:
        result ^= ord(character)
    return f"{result:02X}"


def sentence(body):
    return f"${body}*{checksum(body)}"


def coordinate(value, hemisphere, latitude):
    width, limit = (2, 90) if latitude else (3, 180)
    if not re.fullmatch(r"\d{" + str(width + 2) + r"}(?:\.\d+)?", value):
        raise ValueError("expected degrees followed by minutes")
    degrees, minutes = int(value[:width]), Decimal(value[width:])
    if minutes >= 60 or degrees > limit or (degrees == limit and minutes != 0):
        raise ValueError("coordinate outside valid range")
    if hemisphere not in (("N", "S") if latitude else ("E", "W")):
        raise ValueError("invalid hemisphere")
    result = Decimal(degrees) + minutes / 60
    return float(-result if hemisphere in ("S", "W") else result)


def utc(value):
    if not re.fullmatch(r"\d{6}(?:\.\d+)?", value):
        raise ValueError("expected hhmmss with optional fractional seconds")
    hours, minutes, seconds = int(value[:2]), int(value[2:4]), Decimal(value[4:])
    if hours > 23 or minutes > 59 or seconds >= 61:
        raise ValueError("time outside valid range")
    return f"{value[:2]}:{value[2:4]}:{value[4:]} UTC"


def decode_value(kind, index, value, values):
    if not value:
        return "Not supplied"
    coord_indexes = {"RMC": (2, 4), "GGA": (1, 3)}
    if kind in coord_indexes and index in coord_indexes[kind]:
        latitude = index == coord_indexes[kind][0]
        hemisphere = values[index + 1] if index + 1 < len(values) else ""
        return f"{coordinate(value, hemisphere, latitude):.7f}° (decimal degrees)"
    if (kind in ("RMC", "GGA") and index == 0):
        return utc(value)
    if kind == "RMC" and index == 1:
        if value not in ("A", "V"):
            raise ValueError("expected A or V")
        return "Active / valid status" if value == "A" else "Void / invalid status"
    if kind == "RMC" and index == 8:
        if not re.fullmatch(r"\d{6}", value):
            raise ValueError("expected ddmmyy")
        datetime.strptime(value, "%d%m%y")  # Check calendar validity, without assuming century.
        return f"{value[:2]}/{value[2:4]}/{value[4:]} (DD/MM/YY; century not encoded)"
    if kind == "GGA" and index == 5:
        mapping = {"0": "No valid fix", "1": "Standalone fix", "2": "Differential fix", "3": "PPS fix (legacy)", "4": "RTK fixed", "5": "RTK float", "6": "Estimated / dead reckoning", "7": "Manual input", "8": "Simulation"}
        if value not in mapping:
            raise ValueError("unrecognized fix-quality code")
        return mapping[value]
    if (kind == "RMC" and index == 11) or (kind == "VTG" and index == 8):
        modes = {"A": "Autonomous", "D": "Differential", "E": "Estimated", "M": "Manual", "S": "Simulation", "N": "Not valid", "F": "RTK float", "R": "RTK fixed", "P": "Precise"}
        return modes.get(value, f"Mode {value} (version/device specific)")
    units = {"RMC": {6: "knots", 7: "° true (course over ground)", 9: "°"}, "GGA": {6: "satellites", 7: "(HDOP; dimensionless)", 8: "m (height above mean sea level)", 10: "m (geoid separation)", 12: "s"}, "VTG": {0: "° true (course over ground)", 2: "° magnetic (course over ground)", 4: "knots", 6: "km/h"}, "HDT": {0: "° true (heading)"}}
    unit = units.get(kind, {}).get(index)
    if unit:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("number must be finite")
        angles = (kind == "RMC" and index == 7) or (kind == "VTG" and index in (0, 2)) or (kind == "HDT" and index == 0)
        if angles and not 0 <= number < 360:
            raise ValueError("angle must be at least 0 and less than 360")
        nonnegative = (kind == "RMC" and index in (6, 9)) or (kind == "GGA" and index in (6, 7, 12)) or (kind == "VTG" and index in (4, 6))
        if nonnegative and number < 0:
            raise ValueError("value cannot be negative")
        if kind == "GGA" and index == 6 and not value.isdigit():
            raise ValueError("satellite count must be an integer")
        return f"{number:g} {unit}"
    markers = {"HDT": {1: "T"}, "VTG": {1: "T", 3: "M", 5: "N", 7: "K"}, "GGA": {9: "M", 11: "M"}}
    if index in markers.get(kind, {}) and value != markers[kind][index]:
        raise ValueError(f"expected unit/reference marker {markers[kind][index]}")
    return value


def parse(raw, catalog):
    message = Message(raw=raw.strip())
    text = message.raw
    if not text or text[0] not in "$!":
        message.issues.append("Sentence must begin with $ or !; timestamp prefixes are not accepted.")
        return message
    if not text.isascii() or any(ord(c) < 32 or ord(c) > 126 for c in text):
        message.issues.append("Sentence must contain printable ASCII characters.")
        return message
    body, separator, supplied = text[1:].partition("*")
    message.expected = checksum(body)
    message.supplied = supplied
    if not separator:
        message.checksum = "Missing"
    elif not re.fullmatch(r"[0-9A-Fa-f]{2}", supplied):
        message.checksum = "Malformed"
    elif supplied.upper() == message.expected:
        message.checksum = "Valid"
    else:
        message.checksum = "Mismatch"
    parts = body.split(",")
    address = parts[0]
    if not re.fullmatch(r"[A-Z0-9]{5}", address) or address.startswith("P"):
        message.issues.append("Unsupported address; proprietary sentences are shown as raw data.")
        return message
    message.talker, message.kind = address[:2], address[2:]
    message.values = parts[1:]
    entry = catalog.get(message.kind)
    fields = entry["fields"] if entry else []
    if not entry:
        message.issues.append("No reference definition for this sentence; fields are shown without interpretation.")
    minimums = {"RMC": 11, "GGA": 14, "VTG": 8, "HDT": 2}
    if message.kind in minimums and len(message.values) < minimums[message.kind]:
        message.issues.append(f"Truncated {message.kind}: expected at least {minimums[message.kind]} fields.")
    values = message.values
    if message.kind == "RMC" and len(values) > 1 and values[1] == "V":
        message.issues.append("Receiver reports void / invalid navigation data.")
    if message.kind == "GGA" and len(values) > 5 and values[5] == "0":
        message.issues.append("Receiver reports no valid position fix.")
    mode_index = {"RMC": 11, "VTG": 8}.get(message.kind)
    if mode_index is not None and len(values) > mode_index and values[mode_index] == "N":
        message.issues.append("Receiver mode reports invalid data.")
    required = {"HDT": (0, 1), "VTG": (0, 1, 4, 5, 6, 7)}.get(message.kind, ())
    if message.kind == "RMC" and len(values) > 1 and values[1] == "A":
        required = (0, 2, 3, 4, 5, 6, 7, 8)
    if message.kind == "GGA" and len(values) > 5 and values[5] != "0":
        required = (0, 1, 2, 3, 4, 5, 6, 7)
    for index in required:
        if index < len(values) and not values[index]:
            message.issues.append(f"Field {index + 1} is empty; expected a value for this report.")
    for index, value in enumerate(message.values):
        spec = fields[index] if index < len(fields) else {"name": f"Additional field {index + 1}", "description": "Version/device-specific field; consult the source documentation."}
        try:
            decoded = decode_value(message.kind, index, value, message.values) if entry else value or "Not supplied"
        except (ValueError, InvalidOperation, OverflowError) as exc:
            decoded = f"Invalid: {exc}"
            message.issues.append(f"Field {index + 1}: {exc}")
        message.rows.append((index + 1, spec["name"], value or "(empty)", decoded, spec["description"]))
    return message

import re
from dataclasses import dataclass
from typing import Optional
from ..models.models import SeverityEnum, InboundKind

REPORT_REGEX = re.compile(
    r"^REPORT:\s*(?P<type>[A-Z0-9_]+)\s+at\s+(?P<location>.+?)\s+radius\s+(?P<radius>\d+(?:\.\d+)?)(?P<unit>km|m)\s+severity\s+(?P<severity>LOW|MEDIUM|HIGH)\s*$",
    re.IGNORECASE,
)

@dataclass
class ParsedReport:
    type: str
    location_text: str
    radius_m: int
    severity: SeverityEnum

@dataclass
class ParsedInbound:
    kind: InboundKind
    report: Optional[ParsedReport] = None
    help_text: Optional[str] = None


def parse_inbound(text: str) -> ParsedInbound:
    original = text.strip()
    upper = original.upper()

    if upper.startswith("REPORT:"):
        m = REPORT_REGEX.match(original)
        if not m:
            # malformed report treated as GENERAL
            return ParsedInbound(kind=InboundKind.GENERAL)
        gd = m.groupdict()
        radius_val = float(gd["radius"])
        unit = gd["unit"].lower()
        radius_m = int(radius_val * 1000) if unit == "km" else int(radius_val)
        sev = SeverityEnum(gd["severity"].upper())
        pr = ParsedReport(
            type=gd["type"].upper(),
            location_text=gd["location"].strip(),
            radius_m=radius_m,
            severity=sev,
        )
        return ParsedInbound(kind=InboundKind.REPORT, report=pr)

    if upper.startswith("HELP"):
        rest = original[4:].strip()
        return ParsedInbound(kind=InboundKind.HELP, help_text=rest or None)

    if upper.startswith("SAFE"):
        return ParsedInbound(kind=InboundKind.SAFE)

    return ParsedInbound(kind=InboundKind.GENERAL)

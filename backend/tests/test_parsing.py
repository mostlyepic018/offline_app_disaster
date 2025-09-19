from backend.app.services.parsing import parse_inbound
from backend.app.models.models import InboundKind, SeverityEnum

def test_parse_valid_report():
    msg = "REPORT: FLOOD at MARKET STREET radius 5km severity HIGH"
    parsed = parse_inbound(msg)
    assert parsed.kind == InboundKind.REPORT
    assert parsed.report is not None
    assert parsed.report.radius_m == 5000
    assert parsed.report.severity == SeverityEnum.HIGH


def test_parse_help_with_text():
    msg = "HELP 3 people trapped"
    parsed = parse_inbound(msg)
    assert parsed.kind == InboundKind.HELP
    assert parsed.help_text == "3 people trapped"


def test_parse_general():
    msg = "Random message"
    parsed = parse_inbound(msg)
    assert parsed.kind == InboundKind.GENERAL

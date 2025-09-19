from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_report_and_approve_flow():
    # Submit report
    r = client.post("/receive-sms", json={"from": "+1001", "message": "REPORT: FIRE at CITY CENTER radius 3km severity MEDIUM"})
    assert r.status_code == 200
    rid = r.json()["report_id"]

    # Add a user inside zone
    client.post("/users", json={"phone": "+2001", "last_lat": 10.0, "last_lng": 20.0})

    # Approve with coordinates
    approve = client.post(f"/disasters/{rid}/verify", json={"approve": True, "lat": 10.0, "lng": 20.01})
    assert approve.status_code == 200

    # Outbound messages should exist
    outbound = client.get("/gateway/outbound")
    assert outbound.status_code == 200
    data = outbound.json()
    assert len(data) >= 1
    assert any("ALERT:" in m["body"] for m in data)

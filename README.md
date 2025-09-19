# Offline Disaster Alert & Two-Way SMS Platform

## 1. Vision
A lightweight, offline-capable disaster reporting and alerting system for low-connectivity regions. Citizens use plain SMS to report incidents and receive alerts. Authorities verify, activate, and monitor disasters. Late entrants into an affected zone are still notified. Two‑way SMS (HELP / SAFE / FREEFORM) assists rescue coordination.

## 2. High-Level Architecture
```
+-------------------+      +-------------------------+      +--------------------------+
|  User Phones      | SMS  |  Android SMS Gateway    | HTTP |  Backend (FastAPI)       |
|  (Citizens)       |<---->|  (SMSSync / Termux)     |<---->|  Parsing + Geofencing    |
|  Send REPORT SMS  |      |  Forwards & Sends SMS   |      |  Verification Workflow   |
|  Receive ALERT    |      +-------------------------+      |  Outbound SMS Queue      |
|  Reply HELP/SAFE  |                                   |  Late Entrant Detector    |
+-------------------+                                   +--------------------------+
                                                           |
                                                   +---------------------+
                                                   | Authority UI / CLI  |
                                                   | Review & Approve    |
                                                   | Monitor Responses   |
                                                   +---------------------+
```

## 3. Core Message Formats (Inbound from Citizens)
- Disaster report:
  - `REPORT: <TYPE> at <LOCATION TEXT> radius <NUMBER><km|m> severity <LOW|MEDIUM|HIGH>`
  - Example: `REPORT: FLOOD at MARKET STREET radius 5km severity HIGH`
- Status / help:
  - `HELP` (user requests rescue)
  - `SAFE` (user confirms safety)
  - `HELP <optional free text>` (e.g., `HELP 3 people trapped roof`)
  - Any other text logged as `GENERAL` inbound.

## 4. Entities (Conceptual)
- User (id, phone, last_lat, last_lng, last_tower, updated_at)
- DisasterReport (id, raw_text, type, location_text, lat, lng, radius_m, severity, status=pending|rejected|approved, reporter_phone, created_at)
- DisasterAlert (id, disaster_id FK, activated_at, deactivated_at nullable)
- InboundMessage (id, phone, body, kind=REPORT|HELP|SAFE|GENERAL, linked_disaster_id nullable, created_at)
- HelpRequest (id, inbound_id FK, phone, status=open|ack|resolved, notes)
- OutboundSMS (id, phone, body, purpose=ALERT|ACK|INFO|HELP_CONFIRM, disaster_id nullable, sent_at nullable, attempt_count)
- UserAlertLog (id, disaster_id, user_id, first_sent_at)

## 5. Workflow Summary
1. Citizen sends REPORT → Gateway HTTP POST → `/receive-sms` → parse → create `DisasterReport (pending)` + store raw inbound.
2. Authority lists pending reports → approves one → system creates `DisasterAlert` + computes affected users (geofence) → enqueues SMS alerts.
3. Outbound queue polled by Android gateway (or pushed) → sends each SMS via SIM.
4. HELP / SAFE replies processed into `HelpRequest` or safety status logs.
5. Movement (`/move-user`) triggers re-evaluation: user entering active zone → alert enqueued if not previously alerted.

## 6. Geofencing Strategy
- Use simple Haversine via `geopy.distance` (sufficient for <=100km radii).
- Store disaster epicenter lat/lng + radius (meters).
- Maintain `UserAlertLog` to prevent duplicate alerts per disaster per user.

## 7. Late Entrant Detection
- Endpoint: `POST /move-user` with new lat/lng (or tower id mapping to coordinates).
- Backend: fetch active disasters → for each, if user inside radius AND not in alert log → enqueue alert.

## 8. SMS Gateway Integration (SMSSync style)
- Incoming webhook: `POST /receive-sms` body includes: `{ "from": "+1555123456", "message": "REPORT: FIRE ..." }`
- Outgoing fetch (pull model): Gateway periodically calls `GET /gateway/outbound?limit=20` → returns unsent messages JSON → after each SMS send, gateway `POST /gateway/delivered` (optional future) to mark as sent.
- (Alternatively push model) Backend `POST` to locally exposed gateway endpoint (if on same LAN) at `http://phone-ip:port/sms/send`.

## 9. API (Initial Draft)
- `GET /health` – liveness.
- `POST /receive-sms` – inbound from gateway.
- `GET /disasters/pending` – list unverified reports.
- `GET /disasters/active` – list active disasters.
- `POST /disasters/{id}/verify` – approve or reject: `{ "approve": true }` + optional resolved lat/lng.
- `POST /move-user` – simulate movement: `{ "phone": "+1555..", "lat": 12.34, "lng": 45.67 }`.
- `POST /users` – register or update user location directly.
- `GET /gateway/outbound` – poll unsent messages.
- `POST /messages/help/{id}/ack` – mark help request acknowledged.

## 10. Parsing Rules (Draft)
Regular expression approach for REPORT lines. Steps:
1. Normalize whitespace & upper-case keywords (`REPORT:` prefix).
2. Extract TYPE (alphanumeric/underscore).
3. Extract `at <LOCATION TEXT>` (greedy until ` radius ` token).
4. Extract radius number + unit; convert to meters.
5. Extract severity token (LOW|MEDIUM|HIGH); default MEDIUM if missing.
Fallback: if parsing fails → mark inbound as GENERAL and store original text.

## 11. Tech Stack
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2.x ORM + Alembic (optional later; initial simple metadata.create_all)
- SQLite (hackathon) / PostgreSQL + PostGIS (future)
- geopy (distance) or manual Haversine
- Pydantic v2 for schemas
- pytest for tests

## 12. Directory Layout (Planned)
```
backend/
  app/
    api/                # Routers
    core/               # Config, db, security
    models/             # SQLAlchemy models
    schemas/            # Pydantic models
    services/           # Parsing, geofence, alert logic
    workers/            # (Future) background send / scheduler
    main.py             # FastAPI app factory
  tests/
README.md
```

## 13. Minimal Data Model (First Pass, May Adjust)
```
User
  id (int) / phone (unique str)
  last_lat, last_lng (float nullable)
  last_tower (str nullable)
  updated_at (datetime)

DisasterReport
  id, raw_text, type, location_text, lat, lng, radius_m, severity, status, reporter_phone, created_at

DisasterAlert
  id, disaster_id FK, activated_at, deactivated_at

InboundMessage
  id, phone, body, kind, disaster_id nullable, created_at

HelpRequest
  id, inbound_id FK, phone, status, notes, created_at

OutboundSMS
  id, phone, body, purpose, disaster_id nullable, created_at, sent_at nullable, attempt_count

UserAlertLog
  id, disaster_id, user_id, first_sent_at
```

## 14. Alert Deduplication
- UNIQUE constraint on (disaster_id, user_id) in `UserAlertLog`.
- Before enqueue: check existence; if not present insert and queue message.

## 15. Security / Abuse Considerations (Future)
- Rate limit REPORT messages per phone.
- Authority authentication (API keys / simple token) for verify endpoints.
- Signature/secret between gateway and backend.

## 16. Getting Started (Hackathon Mode)
1. Create virtualenv & install deps (after files added):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
2. Run backend:
```
uvicorn backend.app.main:app --reload
```
3. Simulate inbound REPORT:
```
curl -X POST http://localhost:8000/receive-sms -H "Content-Type: application/json" -d '{"from":"+15550001","message":"REPORT: FLOOD at MARKET STREET radius 5km severity HIGH"}'
```
4. List pending:
```
curl http://localhost:8000/disasters/pending
```
5. Approve disaster (id=1):
```
curl -X POST http://localhost:8000/disasters/1/verify -H "Content-Type: application/json" -d '{"approve":true}'
```
6. Poll outbound (simulate gateway):
```
curl http://localhost:8000/gateway/outbound
```

### Run Tests
After installing dependencies:
```
pytest -q
```

### Simulate Movement Triggering Late Alert
```
curl -X POST http://localhost:8000/move-user -H "Content-Type: application/json" -d '{"phone":"+15550009","lat":10.0,"lng":20.0}'
```

### (New) Run the Gateway Simulator
This does NOT send real SMS; it emulates an Android gateway.
```
python backend/gateway_simulator.py --base-url http://localhost:8000 --interval 5
```
You should see lines like:
```
[SEND] -> +19990001: ALERT: FLOOD near MARKET STREET. Reply HELP if you need assistance.
```

### Linking to a Real Phone Number
In this prototype:
- A citizen phone number is captured when they send an SMS (the gateway webhook populates `from`).
- A user record (`/users`) represents a device's latest known location (phone acts as unique key).
- Outbound alerts currently queue messages for those `User.phone` values inside the geofence.

To deliver real SMS:
1. Install SMSSync (or Termux + termux-api) on an Android with a SIM.
2. Configure SMSSync inbound URL: `http://<your-computer-LAN-IP>:8000/receive-sms`
3. Implement a small poller on the phone (Termux) or adapt a SMSSync custom script to:
  - GET `/gateway/outbound`
  - For each result, send with `termux-sms-send -n <phone> "<body>"`
  - POST IDs to `/gateway/mark-sent`
4. When you send a normal SMS from your phone to the gateway phone's SIM, SMSSync forwards it: backend then associates your number.

Until that gateway is in place, the simulator only prints what WOULD be sent.


## 17. Future Enhancements
- Background worker to batch or retry SMS sending.
- Geo resolving of `location_text` via Nominatim / offline gazetteer.
- Role-based auth & JWT.
- Multi-language alert templates.
- Delivery acknowledgements from gateway.
- Escalation logic (repeat alerts every X minutes if severity HIGH).
- Multi-disaster conflict resolution (dedupe same location & type).

## 18. License & Attribution
MIT (draft) – integrate SMSSync instructions referencing project.

---
Incremental implementation will follow: models, parsing service, routers, and test coverage.

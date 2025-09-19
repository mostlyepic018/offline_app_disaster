from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..core.database import get_db, Base, engine
from ..schemas.schemas import InboundSMSIn, DisasterReportOut, VerifyDisasterRequest, UserCreate, UserOut, OutboundSMSOut, MoveUser, HelpRequestOut
from ..models.models import (
    DisasterReport, InboundMessage, InboundKind, SeverityEnum, ReportStatus, User,
    DisasterAlert, UserAlertLog, OutboundPurpose, OutboundSMS, HelpRequest, HelpStatus
)
from ..services.parsing import parse_inbound
from ..services.geofence import inside_radius
from ..services.sms_gateway import queue_alert, fetch_unsent
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")

# Ensure tables (simple hackathon approach; in prod use Alembic)
Base.metadata.create_all(bind=engine)

@router.post("/receive-sms")
def receive_sms(payload: InboundSMSIn, db: Session = Depends(get_db)):
    parsed = parse_inbound(payload.message)
    inbound = InboundMessage(phone=payload.from_, body=payload.message, kind=parsed.kind)
    db.add(inbound)

    disaster_report = None
    if parsed.kind.name == 'REPORT' and parsed.report:
        dr = DisasterReport(
            raw_text=payload.message,
            type=parsed.report.type,
            location_text=parsed.report.location_text,
            radius_m=parsed.report.radius_m,
            severity=parsed.report.severity,
            status=ReportStatus.pending,
            reporter_phone=payload.from_,
        )
        db.add(dr)
        disaster_report = dr
    elif parsed.kind == InboundKind.HELP:
        # create HelpRequest after commit when we have inbound id (simplify by flushing)
        db.flush()
        hr = HelpRequest(inbound_id=inbound.id, phone=payload.from_)
        db.add(hr)
    elif parsed.kind == InboundKind.SAFE:
        pass  # could log safety confirmation

    db.commit()
    if disaster_report:
        return {"message": "report received", "report_id": disaster_report.id}
    return {"message": "received"}

@router.get("/disasters/pending", response_model=List[DisasterReportOut])
def list_pending(db: Session = Depends(get_db)):
    return db.query(DisasterReport).filter(DisasterReport.status==ReportStatus.pending).all()

@router.get("/disasters/active", response_model=List[DisasterReportOut])
def list_active(db: Session = Depends(get_db)):
    q = db.query(DisasterReport).join(DisasterAlert).filter(DisasterReport.status==ReportStatus.approved, DisasterAlert.deactivated_at.is_(None))
    return q.all()

@router.post("/disasters/{disaster_id}/verify")
def verify_disaster(disaster_id: int, body: VerifyDisasterRequest, db: Session = Depends(get_db)):
    dr = db.query(DisasterReport).filter(DisasterReport.id==disaster_id).first()
    if not dr:
        raise HTTPException(404, "Not found")
    if dr.status != ReportStatus.pending:
        raise HTTPException(400, "Already processed")
    if not body.approve:
        dr.status = ReportStatus.rejected
        db.commit()
        return {"status": "rejected"}
    # Approve
    dr.status = ReportStatus.approved
    if body.lat is not None and body.lng is not None:
        dr.lat = body.lat
        dr.lng = body.lng
    alert = DisasterAlert(disaster_id=dr.id)
    db.add(alert)
    db.flush()

    # compute impacted users
    if dr.lat is not None and dr.lng is not None and dr.radius_m:
        users = db.query(User).filter(User.last_lat.isnot(None), User.last_lng.isnot(None)).all()
        for u in users:
            if inside_radius(dr.lat, dr.lng, u.last_lat, u.last_lng, dr.radius_m):
                # dedupe
                exists = db.query(UserAlertLog).filter_by(disaster_id=dr.id, user_id=u.id).first()
                if not exists:
                    log = UserAlertLog(disaster_id=dr.id, user_id=u.id)
                    db.add(log)
                    queue_alert(db, u.phone, f"ALERT: {dr.type} near {dr.location_text}. Reply HELP if you need assistance.", OutboundPurpose.ALERT, disaster_id=dr.id)
    db.commit()
    return {"status": "approved"}

@router.post("/users", response_model=UserOut)
def create_or_update_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(phone=user.phone).first()
    if existing:
        if user.last_lat is not None: existing.last_lat = user.last_lat
        if user.last_lng is not None: existing.last_lng = user.last_lng
        if user.last_tower is not None: existing.last_tower = user.last_tower
    else:
        existing = User(phone=user.phone, last_lat=user.last_lat, last_lng=user.last_lng, last_tower=user.last_tower)
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing

@router.post("/move-user")
def move_user(m: MoveUser, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(phone=m.phone).first()
    if not user:
        user = User(phone=m.phone)
        db.add(user)
        db.flush()
    user.last_lat = m.lat
    user.last_lng = m.lng

    # Check active disasters
    active = db.query(DisasterReport).join(DisasterAlert).filter(DisasterReport.status==ReportStatus.approved, DisasterAlert.deactivated_at.is_(None))
    new_alerts = 0
    for dr in active:
        if dr.lat and dr.lng and dr.radius_m and user.last_lat and user.last_lng:
            if inside_radius(dr.lat, dr.lng, user.last_lat, user.last_lng, dr.radius_m):
                exists = db.query(UserAlertLog).filter_by(disaster_id=dr.id, user_id=user.id).first()
                if not exists:
                    log = UserAlertLog(disaster_id=dr.id, user_id=user.id)
                    db.add(log)
                    queue_alert(db, user.phone, f"ALERT: {dr.type} near {dr.location_text}. Reply HELP if you need assistance.", OutboundPurpose.ALERT, disaster_id=dr.id)
                    new_alerts += 1
    db.commit()
    return {"status": "ok", "new_alerts": new_alerts}

@router.get("/gateway/outbound", response_model=List[OutboundSMSOut])
def gateway_outbound(limit: int = 50, db: Session = Depends(get_db)):
    msgs = fetch_unsent(db, limit=limit)
    return msgs

@router.post("/gateway/mark-sent")
def gateway_mark_sent(ids: List[int], db: Session = Depends(get_db)):
    from ..services.sms_gateway import mark_sent
    if not ids:
        return {"updated": 0}
    count = mark_sent(db, ids)
    db.commit()
    return {"updated": count}

@router.get("/messages/help", response_model=List[HelpRequestOut])
def list_help(db: Session = Depends(get_db)):
    return db.query(HelpRequest).filter(HelpRequest.status==HelpStatus.open).all()

# ---------- UI (Jinja2) ----------
@router.get("/ui/pending", response_class=HTMLResponse)
def ui_pending(request: Request, db: Session = Depends(get_db)):
    reports = db.query(DisasterReport).filter(DisasterReport.status==ReportStatus.pending).all()
    return templates.TemplateResponse("pending.html", {"request": request, "reports": reports})

@router.get("/ui/active", response_class=HTMLResponse)
def ui_active(request: Request, db: Session = Depends(get_db)):
    reports = db.query(DisasterReport).join(DisasterAlert).filter(DisasterReport.status==ReportStatus.approved, DisasterAlert.deactivated_at.is_(None)).all()
    return templates.TemplateResponse("active.html", {"request": request, "reports": reports})

@router.get("/ui/help", response_class=HTMLResponse)
def ui_help(request: Request, db: Session = Depends(get_db)):
    helps = db.query(HelpRequest).filter(HelpRequest.status==HelpStatus.open).all()
    return templates.TemplateResponse("help.html", {"request": request, "help_requests": helps})

@router.get("/ui/outbound", response_class=HTMLResponse)
def ui_outbound(request: Request, db: Session = Depends(get_db)):
    msgs = db.query(OutboundSMS).order_by(OutboundSMS.id.desc()).limit(200).all()
    return templates.TemplateResponse("outbound.html", {"request": request, "messages": msgs})

@router.post("/ui/approve/{disaster_id}")
def ui_approve(disaster_id: int, lat: float | None = Form(default=None), lng: float | None = Form(default=None), db: Session = Depends(get_db)):
    body = VerifyDisasterRequest(approve=True, lat=lat, lng=lng)
    verify_disaster(disaster_id, body, db)
    return RedirectResponse(url="/ui/pending", status_code=303)

@router.post("/ui/reject/{disaster_id}")
def ui_reject(disaster_id: int, db: Session = Depends(get_db)):
    body = VerifyDisasterRequest(approve=False)
    verify_disaster(disaster_id, body, db)
    return RedirectResponse(url="/ui/pending", status_code=303)

# ---------- SMSSync-compatible inbound (form) ----------
# SMSSync can send fields like: secret, from, message
@router.post("/receive-sms-smssync")
def receive_sms_smssync(from_: str = Form(alias="from"), message: str = Form(...), secret: str | None = Form(default=None), db: Session = Depends(get_db)):
    # TODO: validate secret if configured
    payload = InboundSMSIn(**{"from": from_, "message": message})
    return receive_sms(payload, db)

# ---------- Users UI ----------
@router.get("/ui/users", response_class=HTMLResponse)
def ui_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).limit(500).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.post("/ui/users")
def ui_users_create(phone: str = Form(...), last_lat: float | None = Form(default=None), last_lng: float | None = Form(default=None), last_tower: str | None = Form(default=None), db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(phone=phone).first()
    if existing:
        if last_lat is not None: existing.last_lat = last_lat
        if last_lng is not None: existing.last_lng = last_lng
        if last_tower is not None: existing.last_tower = last_tower
    else:
        existing = User(phone=phone, last_lat=last_lat, last_lng=last_lng, last_tower=last_tower)
        db.add(existing)
    db.commit()
    return RedirectResponse(url="/ui/users", status_code=303)

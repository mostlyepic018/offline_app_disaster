from sqlalchemy.orm import Session
from datetime import datetime
from ..models.models import OutboundSMS, OutboundPurpose


def queue_alert(db: Session, phone: str, body: str, purpose: OutboundPurpose, disaster_id: int | None = None):
    sms = OutboundSMS(phone=phone, body=body, purpose=purpose, disaster_id=disaster_id)
    db.add(sms)
    return sms


def fetch_unsent(db: Session, limit: int = 50):
    return db.query(OutboundSMS).filter(OutboundSMS.sent_at.is_(None)).order_by(OutboundSMS.id.asc()).limit(limit).all()


def mark_sent(db: Session, sms_ids: list[int]):
    now = datetime.utcnow()
    updated = db.query(OutboundSMS).filter(OutboundSMS.id.in_(sms_ids)).all()
    for sms in updated:
        sms.sent_at = now
    return len(updated)

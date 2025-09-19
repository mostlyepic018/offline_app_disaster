from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, UniqueConstraint, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base
import enum

class SeverityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ReportStatus(str, enum.Enum):
    pending = "pending"
    rejected = "rejected"
    approved = "approved"

class InboundKind(str, enum.Enum):
    REPORT = "REPORT"
    HELP = "HELP"
    SAFE = "SAFE"
    GENERAL = "GENERAL"

class HelpStatus(str, enum.Enum):
    open = "open"
    ack = "ack"
    resolved = "resolved"

class OutboundPurpose(str, enum.Enum):
    ALERT = "ALERT"
    ACK = "ACK"
    INFO = "INFO"
    HELP_CONFIRM = "HELP_CONFIRM"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)
    last_tower = Column(String(64), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DisasterReport(Base):
    __tablename__ = "disaster_reports"
    id = Column(Integer, primary_key=True)
    raw_text = Column(Text, nullable=False)
    type = Column(String(64), nullable=True)
    location_text = Column(String(255), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    radius_m = Column(Integer, nullable=True)
    severity = Column(Enum(SeverityEnum), nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending, nullable=False)
    reporter_phone = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    alert = relationship("DisasterAlert", back_populates="disaster", uselist=False)

class DisasterAlert(Base):
    __tablename__ = "disaster_alerts"
    id = Column(Integer, primary_key=True)
    disaster_id = Column(Integer, ForeignKey("disaster_reports.id"), nullable=False)
    activated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deactivated_at = Column(DateTime, nullable=True)

    disaster = relationship("DisasterReport", back_populates="alert")

class InboundMessage(Base):
    __tablename__ = "inbound_messages"
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), index=True, nullable=False)
    body = Column(Text, nullable=False)
    kind = Column(Enum(InboundKind), nullable=False)
    disaster_id = Column(Integer, ForeignKey("disaster_reports.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class HelpRequest(Base):
    __tablename__ = "help_requests"
    id = Column(Integer, primary_key=True)
    inbound_id = Column(Integer, ForeignKey("inbound_messages.id"), nullable=False)
    phone = Column(String(32), index=True, nullable=False)
    status = Column(Enum(HelpStatus), default=HelpStatus.open, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class OutboundSMS(Base):
    __tablename__ = "outbound_sms"
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), index=True, nullable=False)
    body = Column(Text, nullable=False)
    purpose = Column(Enum(OutboundPurpose), nullable=False)
    disaster_id = Column(Integer, ForeignKey("disaster_reports.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)

class UserAlertLog(Base):
    __tablename__ = "user_alert_log"
    id = Column(Integer, primary_key=True)
    disaster_id = Column(Integer, ForeignKey("disaster_reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    first_sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('disaster_id', 'user_id', name='uq_disaster_user'),
    )

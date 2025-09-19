from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.models import SeverityEnum, ReportStatus, InboundKind, HelpStatus, OutboundPurpose

class UserCreate(BaseModel):
    phone: str
    last_lat: Optional[float] = None
    last_lng: Optional[float] = None
    last_tower: Optional[str] = None

class UserOut(BaseModel):
    id: int
    phone: str
    last_lat: Optional[float]
    last_lng: Optional[float]
    last_tower: Optional[str]
    updated_at: datetime
    class Config:
        from_attributes = True

class DisasterReportOut(BaseModel):
    id: int
    raw_text: str
    type: Optional[str]
    location_text: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    radius_m: Optional[int]
    severity: Optional[SeverityEnum]
    status: ReportStatus
    reporter_phone: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class VerifyDisasterRequest(BaseModel):
    approve: bool
    lat: Optional[float] = None
    lng: Optional[float] = None

class InboundSMSIn(BaseModel):
    from_: str = Field(alias="from")
    message: str

class OutboundSMSOut(BaseModel):
    id: int
    phone: str
    body: str
    purpose: OutboundPurpose
    disaster_id: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

class MoveUser(BaseModel):
    phone: str
    lat: float
    lng: float

class HelpRequestOut(BaseModel):
    id: int
    phone: str
    status: HelpStatus
    created_at: datetime
    class Config:
        from_attributes = True

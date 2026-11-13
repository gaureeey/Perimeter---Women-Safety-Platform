from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DeviceTokenRegisterRequest(BaseModel):
    token: str
    platform: Optional[str] = "android"
    device_name: Optional[str] = None

class DeviceTokenResponse(BaseModel):
    status: str
    token: str
    platform: str
    message: str

class NotificationItemResponse(BaseModel):
    id: str
    incident_id: Optional[str] = None
    target_role: str
    title: str
    message: str
    severity: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    approximate_area: Optional[str] = None
    is_read: bool
    created_at: datetime


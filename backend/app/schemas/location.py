"""
PERIMETER Platform - Geolocation Request and Response Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class LocationUpdateRequest(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate between -90 and +90")
    longitude: float = Field(..., description="Longitude coordinate between -180 and +180")
    accuracy: Optional[float] = Field(10.0, ge=0.0, description="Accuracy radius in meters")
    source: Optional[str] = Field("browser_gps", description="Source of the location capture")
    privacy_level: Optional[str] = Field("EMERGENCY", description="PRIVATE, EMERGENCY, PUBLIC_APPROXIMATE, PUBLIC")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v < -90.0 or v > 90.0:
            raise ValueError("Latitude must be between -90 and +90 degrees.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v < -180.0 or v > 180.0:
            raise ValueError("Longitude must be between -180 and +180 degrees.")
        return v

class LocationResponse(BaseModel):
    id: str
    user_id: str
    latitude: float
    longitude: float
    accuracy: float
    timestamp: datetime
    source: str
    is_current: bool
    privacy_level: str

    model_config = {"from_attributes": True}

class ResponderLocationInfo(BaseModel):
    user_id: str
    name: str
    role: str
    badge_title: str
    latitude: float
    longitude: float
    distance_km: Optional[float] = None
    last_updated: datetime
    is_active: bool

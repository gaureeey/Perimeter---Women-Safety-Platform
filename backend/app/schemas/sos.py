from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class LocationCoords(BaseModel):
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = 10.0
    address: Optional[str] = "Live Geolocation Coordinates"

class SOSTriggerRequest(BaseModel):
    user_name: str
    user_id: Optional[str] = None
    phone: Optional[str] = None
    trigger_type: str = "MANUAL_HOLD"  # SHAKE_MOTION, MANUAL_HOLD, AUTO_FALL, VEHICLE_CRASH, ACCIDENT_REPORT
    severity: Optional[str] = "HIGH"
    location: LocationCoords
    battery_percentage: Optional[int] = 85
    notes: Optional[str] = None

class ResponderInfo(BaseModel):
    responder_id: str
    responder_name: str
    role: str  # volunteer, police
    eta_minutes: float
    distance_km: float
    status: str  # EN_ROUTE, ARRIVED, RESOLVED

class SOSIncidentResponse(BaseModel):
    incident_id: str
    user_id: Optional[str] = None
    user_name: str
    trigger_type: str
    severity: Optional[str] = "HIGH"
    notes: Optional[str] = None
    status: str = "ACTIVE_DISPATCH"  # TRIGGERED, ACTIVE_DISPATCH, RESPONDER_ARRIVED, RESOLVED
    created_at: datetime
    location: LocationCoords
    geofence_radius_km: float = 5.0
    active_responders: List[ResponderInfo] = []
    case_id: str

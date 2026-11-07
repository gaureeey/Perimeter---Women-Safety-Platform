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
    trigger_type: str = "MANUAL_HOLD"
    # Severity controls responder priority; all SOS events are visible to police and volunteers.
    severity: Optional[str] = "MEDIUM"
    location: LocationCoords
    battery_percentage: Optional[int] = 85
    notes: Optional[str] = None
    category: Optional[str] = "public"
    audio_proof_url: Optional[str] = None
    video_proof_url: Optional[str] = None
    share_location: bool = True
    record_audio: bool = False
    silent_mode: bool = False

class SOSRoutingInfo(BaseModel):
    dispatch_role: str
    routing_reason: str

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
    dispatch_role: str = "volunteer"
    routing_reason: str = "SOS shared with Police Command and verified volunteers."
    category: Optional[str] = "public"
    audio_proof_url: Optional[str] = None
    video_proof_url: Optional[str] = None

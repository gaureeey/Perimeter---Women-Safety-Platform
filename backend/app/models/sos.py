from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
from app.db.spatial import SpatialPoint, point_to_wkt
import uuid

class SOSIncident(Base):
    __tablename__ = "sos_incidents"

    incident_id = Column(String, primary_key=True, default=lambda: f"SOS-2026-{uuid.uuid4().hex[:4].upper()}")
    user_id = Column(String, nullable=True)
    user_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    trigger_type = Column(String, default="MANUAL_HOLD")  # SHAKE_MOTION, MANUAL_HOLD, AUTO_FALL, ACCIDENT_REPORT
    severity = Column(String, default="HIGH")  # CRITICAL, HIGH, MEDIUM, MINOR
    notes = Column(String, nullable=True)
    status = Column(String, default="ACTIVE_DISPATCH")  # ACTIVE_DISPATCH, ACKNOWLEDGED, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    
    # Coordinates & PostGIS Point
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_point = Column(SpatialPoint, nullable=True)
    accuracy_meters = Column(Float, default=10.0)
    address = Column(String, default="Live GPS Geofence Alert")
    
    geofence_radius_km = Column(Float, default=5.0)
    case_id = Column(String, nullable=False, default=lambda: f"CAS-2026-{uuid.uuid4().hex[:4].upper()}")

    responders = relationship("Responder", back_populates="incident", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.latitude is not None and self.longitude is not None and not self.location_point:
            self.location_point = point_to_wkt(self.latitude, self.longitude)

class Responder(Base):
    __tablename__ = "responders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("sos_incidents.incident_id"), nullable=False)
    responder_id = Column(String, nullable=False)
    responder_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # volunteer, police
    eta_minutes = Column(Float, default=3.5)
    distance_km = Column(Float, default=1.2)
    status = Column(String, default="EN_ROUTE")  # EN_ROUTE, ARRIVED, RESOLVED
    assigned_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("SOSIncident", back_populates="responders")

"""
PERIMETER Platform - User Location Model
Stores real-time and historical geolocation updates with PostGIS spatial point indexing.
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.session import Base
from app.db.spatial import SpatialPoint, point_to_wkt

class UserLocation(Base):
    __tablename__ = "user_locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_point = Column(SpatialPoint, nullable=True)
    accuracy = Column(Float, default=10.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, default="browser_gps")  # browser_gps, mobile_gps, network, manual
    is_current = Column(Boolean, default=True, index=True)
    privacy_level = Column(String, default="EMERGENCY")  # PRIVATE, EMERGENCY, PUBLIC_APPROXIMATE, PUBLIC

    user = relationship("User", backref="location_history")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.latitude is not None and self.longitude is not None and not self.location_point:
            self.location_point = point_to_wkt(self.latitude, self.longitude)

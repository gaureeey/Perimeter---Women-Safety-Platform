"""
PERIMETER Platform - Crime Statistics & Area Safety Score Models
Stores official NCRB crime statistics and computed Perimeter Safety Risk metrics.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime
import uuid
from app.db.session import Base
from app.db.spatial import SpatialPoint, point_to_wkt

class CrimeStatistic(Base):
    __tablename__ = "crime_statistics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    state = Column(String, nullable=False, index=True)
    district = Column(String, nullable=False, index=True)
    city = Column(String, nullable=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    crime_category = Column(String, nullable=False, index=True)  # Crimes Against Women, Rape, Kidnapping & Abduction, Assault on Women, Violent Crime, Cyber Crime
    crime_count = Column(Integer, default=0)
    crime_rate = Column(Float, default=0.0)  # Per 100,000 population
    women_safety_weight = Column(Float, default=1.0)
    violent_crime_weight = Column(Float, default=1.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_point = Column(SpatialPoint, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.latitude is not None and self.longitude is not None and not self.location_point:
            self.location_point = point_to_wkt(self.latitude, self.longitude)


class AreaSafetyScore(Base):
    __tablename__ = "safety_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    area_name = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_point = Column(SpatialPoint, nullable=True)
    risk_score = Column(Float, default=50.0)  # 0 to 100 Perimeter Safety Risk Score
    risk_level = Column(String, default="MODERATE_REPORTED_RISK")  # LOWER_REPORTED_RISK, MODERATE_REPORTED_RISK, HIGH_REPORTED_RISK
    incident_count = Column(Integer, default=0)
    crime_trend = Column(String, default="STABLE")  # DECREASING, STABLE, INCREASING
    ncrb_baseline_score = Column(Float, default=50.0)
    perimeter_incident_score = Column(Float, default=0.0)
    data_sources = Column(String, default="Perimeter incidents, NCRB")
    last_calculated_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.latitude is not None and self.longitude is not None and not self.location_point:
            self.location_point = point_to_wkt(self.latitude, self.longitude)

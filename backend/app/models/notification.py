"""
PERIMETER Platform - Notification Model
Stores targeted emergency dispatches and safety bulletins across Police, Volunteers, Journalists, and Citizens.
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
import uuid
from app.db.session import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: f"notif_{uuid.uuid4().hex[:8]}")
    recipient_user_id = Column(String, nullable=True, index=True)
    target_role = Column(String, nullable=False, index=True)  # police, volunteer, journalist, user, all
    incident_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String, default="HIGH")  # CRITICAL, HIGH, MEDIUM, INFO
    
    # Authorized Location Data (Filtered based on recipient role)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    approximate_area = Column(String, nullable=True)  # Privacy-safe for journalists / feed
    
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

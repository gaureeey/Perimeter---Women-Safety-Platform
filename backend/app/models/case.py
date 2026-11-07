from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import uuid

class IncidentCase(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, default=lambda: f"CAS-2026-{uuid.uuid4().hex[:4].upper()}")
    user_id = Column(String, nullable=True)  # Associated user account ID
    title = Column(String, nullable=False)
    victim_identifier = Column(String, nullable=False)
    status = Column(String, default="ACTIVE_INVESTIGATION")  # ACTIVE_INVESTIGATION, ACTIVE_DISPATCH, RESOLVED, ARCHIVED
    priority = Column(String, default="HIGH")  # CRITICAL, HIGH, MEDIUM
    location = Column(String, nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow)
    assigned_precinct = Column(String, default="Central Police Precinct #01")

    timeline_events = relationship("TimelineEvent", back_populates="case", cascade="all, delete-orphan")
    linked_press_reports = relationship("LinkedPressArticle", back_populates="case", cascade="all, delete-orphan")

class TimelineEvent(Base):
    __tablename__ = "case_timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.case_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)  # citizen, volunteer, police, journalist
    actor_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("IncidentCase", back_populates="timeline_events")

class LinkedPressArticle(Base):
    __tablename__ = "linked_press_articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.case_id"), nullable=False)
    article_id = Column(String, nullable=False, default=lambda: f"art_{uuid.uuid4().hex[:4]}")
    title = Column(String, nullable=False)
    outlet = Column(String, nullable=False)
    journalist_name = Column(String, nullable=False)
    url = Column(String, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("IncidentCase", back_populates="linked_press_reports")

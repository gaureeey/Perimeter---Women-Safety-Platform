from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TimelineEntry(BaseModel):
    timestamp: datetime
    title: str
    description: str
    actor_role: str  # citizen, volunteer, police, journalist
    actor_name: str

class PressArticleLink(BaseModel):
    article_id: str
    title: str
    outlet: str
    journalist_name: str
    url: Optional[str] = None
    published_at: datetime

class CaseResponse(BaseModel):
    case_id: str
    title: str
    victim_identifier: str
    status: str  # ACTIVE_INVESTIGATION, PATROL_DISPATCHED, RESOLVED, ARCHIVED
    priority: str  # HIGH, CRITICAL, MEDIUM
    location: str
    opened_at: datetime
    assigned_precinct: str = "Central Police Precinct #01"
    timeline: List[TimelineEntry] = []
    linked_press_reports: List[PressArticleLink] = []

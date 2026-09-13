"""
PERIMETER Admin Management Schemas
"""
from typing import List, Dict, Any
from pydantic import BaseModel
from app.schemas.auth import UserProfileResponse

class AdminStatsResponse(BaseModel):
    total_users: int
    users_by_role: Dict[str, int]
    active_sos_incidents: int
    resolved_incidents: int
    total_feed_posts: int
    total_cases: int

class SystemStatusResponse(BaseModel):
    status: str
    geofence_engine: str
    database: str
    active_users: int
    active_alerts: int

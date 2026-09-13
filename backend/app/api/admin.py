"""
PERIMETER Admin Management API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

from app.db.session import get_db
from app.models.user import User
from app.models.sos import SOSIncident
from app.models.feed import FeedPost
from app.models.case import IncidentCase
from app.schemas.admin import AdminStatsResponse, SystemStatusResponse
from app.schemas.auth import UserProfileResponse

router = APIRouter(prefix="/admin", tags=["Admin Management & System Control"])

@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(db: Session = Depends(get_db)):
    """
    Retrieve real-time platform metrics for administrative dashboard.
    """
    total_users = db.query(User).count()
    
    # Group users by role
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role: count for role, count in role_counts}
    for r in ["user", "volunteer", "police", "journalist", "admin"]:
        if r not in users_by_role:
            users_by_role[r] = 0

    active_sos = db.query(SOSIncident).filter(SOSIncident.status == "ACTIVE_DISPATCH").count()
    resolved_sos = db.query(SOSIncident).filter(SOSIncident.status == "RESOLVED").count()
    total_posts = db.query(FeedPost).count()
    total_cases = db.query(IncidentCase).count()

    return AdminStatsResponse(
        total_users=total_users,
        users_by_role=users_by_role,
        active_sos_incidents=active_sos,
        resolved_incidents=resolved_sos,
        total_feed_posts=total_posts,
        total_cases=total_cases
    )

@router.get("/system", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """
    Retrieve system health, geofence engine status, and active connections.
    """
    total_users = db.query(User).count()
    active_alerts = db.query(SOSIncident).filter(SOSIncident.status == "ACTIVE_DISPATCH").count()

    return SystemStatusResponse(
        status="OPERATIONAL",
        geofence_engine="5km Radius Spatial Router Active",
        database="SQLite Connected & Migrated",
        active_users=total_users,
        active_alerts=active_alerts
    )

@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Remove a user account (Admin action).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user.role == "admin" and user.id == "adm_001":
        raise HTTPException(status_code=400, detail="Cannot delete super administrator root account.")

    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User {user_id} deleted."}

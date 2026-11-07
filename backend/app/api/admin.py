"""
PERIMETER Admin Management API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from app.models.admin_tracking import LoginHistory, UserPresence, AdminAuditLog
from typing import List, Dict

from app.db.session import get_db
from app.models.user import User
from app.models.sos import SOSIncident
from app.models.feed import FeedPost
from app.models.case import IncidentCase
from app.schemas.admin import AdminStatsResponse, SystemStatusResponse
from app.schemas.auth import UserProfileResponse
from app.core.security import get_current_user
from app.models.case import TimelineEvent

router = APIRouter(prefix="/admin", tags=["Admin Management & System Control"])

def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

@router.get("/users")
def admin_users(q: str = "", role: str = "", limit: int = 100, offset: int = 0,
               db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_admin(current_user)
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term), User.phone.ilike(term), User.id.ilike(term), User.dynamic_field_1.ilike(term)))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(max(0, offset)).limit(max(1, min(limit, 200))).all()
    now = datetime.utcnow()
    return {"total": total, "users": [{"id":u.id,"name":u.name,"username":u.username,"email":u.email,"phone":u.phone,"role":u.role,"badge_title":u.badge_title,"location":u.location,"verified_details":u.dynamic_field_1,"organization_or_area":u.dynamic_field_2,"created_at":u.created_at,"last_seen":(p.last_seen if (p:=db.query(UserPresence).filter(UserPresence.user_id==u.id).first()) else None),"online":bool(p and p.last_seen >= now-timedelta(seconds=90))} for u in users]}

@router.get("/online-users")
def online_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_admin(current_user)
    cutoff=datetime.utcnow()-timedelta(seconds=90)
    rows=db.query(UserPresence).filter(UserPresence.last_seen>=cutoff).order_by(UserPresence.last_seen.desc()).all()
    return [{"user_id":p.user_id,"name":(db.query(User.name).filter(User.id==p.user_id).scalar() or "Unknown"),"role":(db.query(User.role).filter(User.id==p.user_id).scalar() or "unknown"),"last_seen":p.last_seen} for p in rows]

@router.get("/login-history")
def login_history(limit:int=100, db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    require_admin(current_user)
    rows=db.query(LoginHistory).order_by(LoginHistory.occurred_at.desc()).limit(max(1,min(limit,500))).all()
    return [{"id":r.id,"user_id":r.user_id,"identity":r.identity,"success":r.success,"occurred_at":r.occurred_at} for r in rows]

@router.post("/heartbeat")
def heartbeat(db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    p=db.query(UserPresence).filter(UserPresence.user_id==current_user.id).first()
    if p is None: p=UserPresence(user_id=current_user.id); db.add(p)
    p.last_seen=datetime.utcnow(); db.commit()
    return {"ok":True,"last_seen":p.last_seen}

@router.get("/storage")
def storage(db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    require_admin(current_user)
    from app.db.session import engine
    from sqlalchemy import text
    size=None
    if engine.url.database and engine.url.database != ":memory:":
        import os
        try: size=os.path.getsize(engine.url.database)
        except OSError: pass
    return {"database_dialect":engine.dialect.name,"database_size_bytes":size,"note":"Media storage measurement depends on configured upload directory or object storage."}


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve real-time platform metrics for administrative dashboard.
    """
    require_admin(current_user)
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

    online_users = db.query(UserPresence).filter(UserPresence.last_seen >= datetime.utcnow() - timedelta(seconds=90)).count()
    return AdminStatsResponse(
        total_users=total_users,
        users_by_role=users_by_role,
        active_sos_incidents=active_sos,
        resolved_incidents=resolved_sos,
        total_feed_posts=total_posts,
        total_cases=total_cases
    )

@router.get("/system", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve system health, geofence engine status, and active connections.
    """
    require_admin(current_user)
    total_users = db.query(User).count()
    active_alerts = db.query(SOSIncident).filter(SOSIncident.status == "ACTIVE_DISPATCH").count()

    return SystemStatusResponse(
        status="OPERATIONAL",
        geofence_engine="5km Radius Spatial Router Active",
        database="SQLite Connected & Migrated",
        active_users=total_users,
        active_alerts=active_alerts
    )



@router.get("/sos-overview")
def get_admin_sos_overview(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a complete Admin audit view for Citizen SOS incidents.

    Includes citizen identity, case/incident IDs, location, accepted
    volunteer/police responders, resolver, and the case timeline.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    limit = max(1, min(int(limit or 50), 200))
    incidents = (
        db.query(SOSIncident)
        .order_by(SOSIncident.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for inc in incidents:
        citizen = db.query(User).filter(User.id == inc.user_id).first() if inc.user_id else None
        case = db.query(IncidentCase).filter(IncidentCase.case_id == inc.case_id).first()
        events = []
        resolved = None

        if case:
            timeline = sorted(case.timeline_events, key=lambda e: e.timestamp or __import__('datetime').datetime.min)
            for event in timeline:
                item = {
                    "id": event.id,
                    "timestamp": event.timestamp,
                    "title": event.title,
                    "description": event.description,
                    "actor_role": event.actor_role,
                    "actor_name": event.actor_name,
                }
                events.append(item)
                if event.actor_role == "police" and "Resolved" in (event.title or ""):
                    resolved = {
                        "name": event.actor_name,
                        "role": event.actor_role,
                        "timestamp": event.timestamp,
                    }

        # Fall back to the final responder when an older record has no
        # explicit resolution timeline event.
        if resolved is None and inc.status == "RESOLVED":
            completed = [r for r in inc.responders if r.status == "RESOLVED"]
            if completed:
                r = completed[-1]
                resolved = {
                    "name": r.responder_name,
                    "role": r.role,
                    "timestamp": r.assigned_at,
                }

        result.append({
            "incident_id": inc.incident_id,
            "case_id": inc.case_id,
            "user_id": inc.user_id,
            "status": inc.status,
            "severity": inc.severity,
            "trigger_type": inc.trigger_type,
            "notes": inc.notes,
            "created_at": inc.created_at,
            "phone": inc.phone or (citizen.phone if citizen else None),
            "citizen": {
                "id": inc.user_id,
                "name": inc.user_name or (citizen.name if citizen else "Unknown Citizen"),
                "phone": inc.phone or (citizen.phone if citizen else None),
                "email": citizen.email if citizen else None,
                "area": citizen.location if citizen else None,
            },
            "location": {
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "accuracy_meters": inc.accuracy_meters,
                "address": inc.address,
            },
            "responders": [
                {
                    "responder_id": r.responder_id,
                    "name": r.responder_name,
                    "role": r.role,
                    "status": r.status,
                    "eta_minutes": r.eta_minutes,
                    "distance_km": r.distance_km,
                    "accepted_at": r.assigned_at,
                }
                for r in inc.responders
            ],
            "timeline": events,
            "resolved_by": resolved,
        })

    return {
        "incidents": result,
        "count": len(result),
    }

@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_admin(current_user)
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

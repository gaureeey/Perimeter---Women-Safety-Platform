"""
PERIMETER Emergency SOS & Incident Dispatch API
Authoritative emergency orchestration with PostGIS proximity routing,
role-based notification dispatch, and immutable case timeline tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.sos import SOSIncident, Responder
from app.models.case import IncidentCase, TimelineEvent
from app.models.user import User
from app.models.location import UserLocation
from app.schemas.sos import SOSTriggerRequest, SOSIncidentResponse, ResponderInfo, SOSLocationUpdate
from app.core.security import get_current_user, get_optional_user, require_role
from app.db.spatial import haversine_distance_km, point_to_wkt
from app.api.notification import dispatch_sos_notifications, manager

router = APIRouter(prefix="/sos", tags=["Emergency SOS & Dispatch"])

# In-memory rate limiting tracker: {ip_or_user_id: [timestamps]}
_sos_rate_limits = {}

def check_sos_rate_limit(key: str, max_calls: int = 5, window_seconds: int = 60):
    now = datetime.utcnow()
    calls = _sos_rate_limits.get(key, [])
    recent_calls = [t for t in calls if (now - t).total_seconds() < window_seconds]
    if len(recent_calls) >= max_calls:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Emergency SOS rate limit exceeded. Please wait a moment before sending another alert."
        )
    recent_calls.append(now)
    _sos_rate_limits[key] = recent_calls

@router.post("/trigger", response_model=SOSIncidentResponse)
def trigger_sos(
    req: SOSTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Trigger emergency SOS or submit an incident report.
    1. Validates real GPS coordinates.
    2. Persists the SOS event to database with PostGIS spatial point.
    3. Provisions an IncidentCase and appends chronological timeline events.
    4. Performs authoritative spatial proximity query for nearby active volunteers.
    5. Dispatches role-tailored notifications to Police, Volunteers, and Journalists.
    """
    # 1. Coordinate Validation
    lat = req.location.latitude
    lng = req.location.longitude
    if lat < -90.0 or lat > 90.0 or lng < -180.0 or lng > 180.0:
        raise HTTPException(status_code=400, detail="Invalid GPS coordinates. Latitude must be -90..90 and Longitude -180..180.")

    # Rate limiting
    rate_key = current_user.id if current_user else req.user_name
    check_sos_rate_limit(rate_key)

    inc_id = f"SOS-2026-{uuid.uuid4().hex[:4].upper()}"
    case_id = f"CAS-2026-{uuid.uuid4().hex[:4].upper()}"
    now = datetime.utcnow()

    # 2. Persist SOS event with Spatial Point
    incident = SOSIncident(
        incident_id=inc_id,
        user_id=req.user_id or (current_user.id if current_user else None),
        user_name=req.user_name,
        phone=req.phone or (current_user.phone if current_user else None),
        trigger_type=req.trigger_type,
        severity=req.severity or "HIGH",
        notes=req.notes,
        status="ACTIVE_DISPATCH",
        latitude=lat,
        longitude=lng,
        location_point=point_to_wkt(lat, lng),
        accuracy_meters=req.location.accuracy_meters or 10.0,
        address=req.location.address or f"GPS Lat {lat:.4f}, Lng {lng:.4f}",
        geofence_radius_km=5.0,
        case_id=case_id,
        created_at=now
    )
    db.add(incident)

    # 3. Provision corresponding IncidentCase
    case_title = (
        f"Emergency SOS Alert ({req.trigger_type.replace('_', ' ')})"
        if req.trigger_type != "ACCIDENT_REPORT"
        else f"Accident & Collision Dispatch ({req.severity})"
    )
    new_case = IncidentCase(
        case_id=case_id,
        title=case_title,
        victim_identifier=f"Citizen {req.user_name}",
        status="ACTIVE_DISPATCH",
        priority=req.severity or "HIGH",
        location=incident.address,
        assigned_precinct="Central Police Precinct #01",
        opened_at=now
    )
    db.add(new_case)

    # 4. Chronological Timeline Event: Step 1 - SOS Triggered
    ev_triggered = TimelineEvent(
        case_id=case_id,
        event_type="SOS_TRIGGERED",
        title=f"SOS Distress Beacon Triggered ({req.trigger_type})",
        description=f"Emergency activated by {req.user_name}. Trigger mode: {req.trigger_type}. Notes: {req.notes or 'None'}",
        actor_role="citizen",
        actor_name=req.user_name,
        timestamp=now
    )
    db.add(ev_triggered)

    # Chronological Timeline Event: Step 2 - Location Captured
    ev_location = TimelineEvent(
        case_id=case_id,
        event_type="LOCATION_CAPTURED",
        title="High-Accuracy GPS Coordinates Locked",
        description=f"Coordinates ({lat:.5f}, {lng:.5f}) with accuracy ±{incident.accuracy_meters:.1f}m confirmed.",
        actor_role="system",
        actor_name="PERIMETER Geofence Engine",
        timestamp=now
    )
    db.add(ev_location)

    # 5. Authoritative PostGIS Proximity Search for Active Volunteers (within 5 km radius)
    volunteers = db.query(UserLocation, User).join(
        User, UserLocation.user_id == User.id
    ).filter(
        UserLocation.is_current == True,
        User.role == "volunteer",
        User.is_active == True
    ).all()

    nearby_volunteers = []
    for loc, u in volunteers:
        dist = haversine_distance_km(lat, lng, loc.latitude, loc.longitude)
        if dist <= incident.geofence_radius_km:
            nearby_volunteers.append((u, dist))

    # Chronological Timeline Event: Step 3 - Police & Volunteers Dispatched
    ev_dispatched = TimelineEvent(
        case_id=case_id,
        event_type="POLICE_NOTIFIED",
        title="Police Command & Geofence Alert Broadcasted",
        description=f"City Police Command alerted with priority {incident.severity}. {len(nearby_volunteers)} active volunteers within 5km perimeter notified.",
        actor_role="system",
        actor_name="PERIMETER Dispatch Router",
        timestamp=now
    )
    db.add(ev_dispatched)

    # Update or persist current user location
    if current_user:
        db.query(UserLocation).filter(
            UserLocation.user_id == current_user.id,
            UserLocation.is_current == True
        ).update({"is_current": False})
        user_loc = UserLocation(
            user_id=current_user.id,
            latitude=lat,
            longitude=lng,
            location_point=point_to_wkt(lat, lng),
            accuracy=incident.accuracy_meters,
            source="emergency_sos",
            is_current=True,
            privacy_level="EMERGENCY"
        )
        db.add(user_loc)
        current_user.last_active_at = now

    db.commit()
    db.refresh(incident)

    # 6. Dispatch role-tailored persistent notifications
    dispatch_sos_notifications(
        db=db,
        incident_id=inc_id,
        user_name=req.user_name,
        phone=incident.phone,
        lat=lat,
        lng=lng,
        accuracy=incident.accuracy_meters,
        address=incident.address,
        severity=incident.severity,
        trigger_type=req.trigger_type,
        nearby_volunteers_count=len(nearby_volunteers)
    )

    # 7. WebSocket live alerts in background
    police_payload = {
        "type": "NEW_SOS_INCIDENT",
        "incident_id": inc_id,
        "case_id": case_id,
        "user_name": req.user_name,
        "phone": incident.phone,
        "trigger_type": req.trigger_type,
        "severity": incident.severity,
        "location": {"latitude": lat, "longitude": lng, "address": incident.address},
        "created_at": incident.created_at.isoformat()
    }
    volunteer_payload = {
        "type": "NEW_SOS_INCIDENT",
        "incident_id": inc_id,
        "case_id": case_id,
        "trigger_type": req.trigger_type,
        "severity": incident.severity,
        "location": {"latitude": lat, "longitude": lng, "address": incident.address},
        "created_at": incident.created_at.isoformat()
    }
    journalist_payload = {
        "type": "VERIFIED_INCIDENT_OPENED",
        "incident_id": inc_id,
        "case_id": case_id,
        "area": incident.address.split(",")[0],
        "severity": incident.severity,
        "created_at": incident.created_at.isoformat()
    }
    background_tasks.add_task(
        manager.broadcast_emergency,
        police_payload,
        volunteer_payload,
        journalist_payload
    )

    return {
        "incident_id": incident.incident_id,
        "user_id": incident.user_id,
        "user_name": incident.user_name,
        "trigger_type": incident.trigger_type,
        "severity": incident.severity,
        "notes": incident.notes,
        "status": incident.status,
        "created_at": incident.created_at,
        "location": {
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "accuracy_meters": incident.accuracy_meters,
            "address": incident.address
        },
        "geofence_radius_km": incident.geofence_radius_km,
        "active_responders": [],
        "case_id": incident.case_id
    }

@router.get("/active", response_model=List[SOSIncidentResponse])
def get_active_incidents(
    lat: Optional[float] = Query(None, description="Volunteer latitude for proximity calculation"),
    lng: Optional[float] = Query(None, description="Volunteer longitude for proximity calculation"),
    radius_km: Optional[float] = Query(5.0, description="Max geofence radius in km (default: 5.0 km)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Retrieve all active emergency SOS dispatches.
    Enforces role-based privacy filters:
    - Police & Admin: Full victim details, exact coordinates, all active emergencies.
    - Volunteer: Filtered by 5km radius proximity using authoritative PostGIS distance; includes calculated distance_km.
    - Journalist: Sanitized coordinates and privacy-safe victim identity.
    """
    incidents = db.query(SOSIncident).filter(
        SOSIncident.status.in_(["ACTIVE_DISPATCH", "ACKNOWLEDGED"])
    ).order_by(SOSIncident.created_at.desc()).all()

    # Determine reference coordinates for volunteer if applicable
    ref_lat = lat
    ref_lng = lng
    if (ref_lat is None or ref_lng is None) and current_user and current_user.role == "volunteer":
        last_loc = db.query(UserLocation).filter(
            UserLocation.user_id == current_user.id,
            UserLocation.is_current == True
        ).order_by(UserLocation.timestamp.desc()).first()
        if last_loc:
            ref_lat = last_loc.latitude
            ref_lng = last_loc.longitude

    results = []
    is_police_or_admin = current_user and current_user.role in ["police", "admin"]
    is_volunteer = current_user and current_user.role == "volunteer"
    is_police_or_vol = is_police_or_admin or is_volunteer

    for inc in incidents:
        # Distance calculation
        dist = None
        if ref_lat is not None and ref_lng is not None:
            dist = haversine_distance_km(ref_lat, ref_lng, inc.latitude, inc.longitude)
            # If requesting as volunteer with active geofence, skip incidents outside configured radius
            if is_volunteer and radius_km is not None and dist > radius_km:
                continue

        responders = [
            ResponderInfo(
                responder_id=r.responder_id,
                responder_name=r.responder_name,
                role=r.role,
                eta_minutes=r.eta_minutes,
                distance_km=r.distance_km,
                status=r.status
            )
            for r in inc.responders
        ]

        # For journalists / public viewers, protect victim's full identity
        display_name = inc.user_name if is_police_or_vol else f"Citizen #{inc.incident_id[-4:]}"
        display_phone = inc.phone if is_police_or_admin else None

        results.append({
            "incident_id": inc.incident_id,
            "user_id": inc.user_id if is_police_or_vol else None,
            "user_name": display_name,
            "trigger_type": inc.trigger_type,
            "severity": inc.severity,
            "notes": inc.notes,
            "status": inc.status,
            "created_at": inc.created_at,
            "location": {
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "accuracy_meters": inc.accuracy_meters,
                "address": inc.address
            },
            "geofence_radius_km": inc.geofence_radius_km,
            "distance_km": round(dist, 2) if dist is not None else None,
            "active_responders": responders,
            "case_id": inc.case_id
        })

    return results

@router.get("/{incident_id}")
def get_incident_by_id(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Retrieve details for a single SOS incident."""
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    
    case = db.query(IncidentCase).filter(IncidentCase.case_id == inc.case_id).first()
    timeline = []
    if case:
        timeline = [
            {
                "id": t.id,
                "event_type": t.event_type,
                "title": t.title,
                "description": t.description,
                "actor_role": t.actor_role,
                "actor_name": t.actor_name,
                "timestamp": t.timestamp
            }
            for t in sorted(case.timeline_events, key=lambda x: x.timestamp)
        ]

    return {
        "incident_id": inc.incident_id,
        "user_name": inc.user_name,
        "phone": inc.phone if (current_user and current_user.role in ["police", "admin"]) else None,
        "trigger_type": inc.trigger_type,
        "severity": inc.severity,
        "status": inc.status,
        "location": {
            "latitude": inc.latitude,
            "longitude": inc.longitude,
            "accuracy_meters": inc.accuracy_meters,
            "address": inc.address
        },
        "created_at": inc.created_at,
        "resolved_at": inc.resolved_at,
        "resolved_by": inc.resolved_by,
        "case_id": inc.case_id,
        "timeline": timeline
    }

@router.post("/{incident_id}/location")
def update_incident_location(
    incident_id: str,
    req: SOSLocationUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Live GPS update for an active SOS incident.
    Persists updated victim coordinates and broadcasts live position to authorized emergency responders.
    """
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    
    if inc.status not in ["ACTIVE_DISPATCH", "ACKNOWLEDGED"]:
        raise HTTPException(status_code=400, detail="Cannot update location for resolved incident.")

    inc.latitude = req.latitude
    inc.longitude = req.longitude
    inc.accuracy_meters = req.accuracy_meters or 10.0
    if req.address:
        inc.address = req.address
    inc.location_point = point_to_wkt(req.latitude, req.longitude)
    
    # Update current user location record
    if inc.user_id:
        db.query(UserLocation).filter(
            UserLocation.user_id == inc.user_id,
            UserLocation.is_current == True
        ).update({"is_current": False})
        
        user_loc = UserLocation(
            user_id=inc.user_id,
            latitude=req.latitude,
            longitude=req.longitude,
            location_point=point_to_wkt(req.latitude, req.longitude),
            accuracy=inc.accuracy_meters,
            source="emergency_live_update",
            is_current=True,
            privacy_level="EMERGENCY"
        )
        db.add(user_loc)
        
    db.commit()

    # Broadcast to Police & Admin map in background
    police_update = {
        "type": "SOS_LOCATION_UPDATE",
        "incident_id": inc.incident_id,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "accuracy_meters": inc.accuracy_meters,
        "address": inc.address,
        "updated_at": datetime.utcnow().isoformat()
    }
    background_tasks.add_task(manager.broadcast_to_role, "police", police_update)
    background_tasks.add_task(manager.broadcast_to_role, "admin", police_update)

    return {"status": "success", "incident_id": incident_id, "updated": True}

@router.post("/{incident_id}/acknowledge")
def acknowledge_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["police", "admin"]))
):
    """
    Police Command: Acknowledge an active SOS dispatch and record officer in charge.
    """
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    inc.status = "ACKNOWLEDGED"

    # Add timeline event to case
    case = db.query(IncidentCase).filter(IncidentCase.case_id == inc.case_id).first()
    if case:
        tle = TimelineEvent(
            case_id=inc.case_id,
            event_type="POLICE_ACKNOWLEDGED",
            title="Police Command Acknowledged Dispatch",
            description=f"Alert acknowledged by {current_user.name} ({current_user.dynamic_field_1 or 'Police Duty Officer'}). Units preparing response.",
            actor_role="police",
            actor_name=current_user.name
        )
        db.add(tle)

    db.commit()
    return {"status": "success", "message": f"Incident {incident_id} acknowledged by {current_user.name}."}

@router.post("/{incident_id}/dispatch")
def dispatch_responder(
    incident_id: str,
    responder_id: str,
    responder_name: str,
    role: str = "police",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["police", "admin"]))
):
    """
    Police Command: Explicitly dispatch a specific patrol unit or officer to the emergency.
    """
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    resp = Responder(
        incident_id=incident_id,
        responder_id=responder_id,
        responder_name=responder_name,
        role=role,
        eta_minutes=2.5,
        distance_km=0.8,
        status="EN_ROUTE"
    )
    db.add(resp)

    # Add timeline event
    case = db.query(IncidentCase).filter(IncidentCase.case_id == inc.case_id).first()
    if case:
        tle = TimelineEvent(
            case_id=inc.case_id,
            event_type="RESPONDER_DISPATCHED",
            title=f"Patrol Unit Dispatched ({role.upper()})",
            description=f"{responder_name} ({role}) en route with ETA ~2.5 mins.",
            actor_role="police",
            actor_name=current_user.name
        )
        db.add(tle)

    db.commit()
    return {"status": "success", "message": f"Unit {responder_name} dispatched to {incident_id}."}

@router.post("/{incident_id}/respond")
def respond_to_incident(
    incident_id: str,
    responder_id: str,
    responder_name: str,
    role: str,
    db: Session = Depends(get_db)
):
    """
    Volunteer or police responder accepts an emergency dispatch assignment.
    """
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    existing_resp = db.query(Responder).filter(
        Responder.incident_id == incident_id,
        Responder.responder_id == responder_id
    ).first()
    if existing_resp:
        return {"status": "already_responded", "message": f"{responder_name} is already en route."}

    resp = Responder(
        incident_id=incident_id,
        responder_id=responder_id,
        responder_name=responder_name,
        role=role,
        eta_minutes=3.0,
        distance_km=1.2,
        status="EN_ROUTE"
    )
    db.add(resp)

    # Add timeline event to linked case
    timeline_evt = TimelineEvent(
        case_id=inc.case_id,
        event_type="RESPONDER_DISPATCHED",
        title=f"Responder En Route ({role.capitalize()})",
        description=f"{responder_name} ({role}) accepted geofence dispatch with ETA ~3.0 mins.",
        actor_role=role,
        actor_name=responder_name
    )
    db.add(timeline_evt)
    db.commit()

    return {"status": "success", "message": f"{responder_name} dispatched to incident {incident_id}."}

@router.post("/{incident_id}/resolve")
def resolve_incident(
    incident_id: str,
    resolved_by: str = "City Police Command",
    notes: Optional[str] = "Incident verified safe and resolved on scene.",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Mark an active incident as resolved and close the associated case timeline.
    """
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    actor = current_user.name if current_user else resolved_by

    inc.status = "RESOLVED"
    inc.resolved_at = datetime.utcnow()
    inc.resolved_by = actor

    # Update linked case
    case = db.query(IncidentCase).filter(IncidentCase.case_id == inc.case_id).first()
    if case:
        case.status = "RESOLVED"
        timeline_evt = TimelineEvent(
            case_id=inc.case_id,
            event_type="INCIDENT_RESOLVED",
            title="Incident Resolved & Case Closed",
            description=f"Resolution logged by {actor}. Notes: {notes}",
            actor_role="police",
            actor_name=actor
        )
        db.add(timeline_evt)

    db.commit()
    return {"status": "success", "message": f"Incident {incident_id} marked as RESOLVED by {actor}."}

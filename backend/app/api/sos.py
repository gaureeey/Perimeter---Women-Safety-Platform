"""
PERIMETER Emergency SOS & Incident Dispatch API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.sos import SOSIncident, Responder
from app.models.case import IncidentCase, TimelineEvent
from app.schemas.sos import SOSTriggerRequest, SOSIncidentResponse, ResponderInfo

router = APIRouter(prefix="/sos", tags=["Emergency SOS & Dispatch"])

@router.post("/trigger", response_model=SOSIncidentResponse)
def trigger_sos(req: SOSTriggerRequest, db: Session = Depends(get_db)):
    """
    Trigger emergency SOS or submit an incident report.
    Persists the incident to the database and automatically provisions an
    immutable IncidentCase with its initial timeline audit event.
    """
    inc_id = f"SOS-2026-{uuid.uuid4().hex[:4].upper()}"
    case_id = f"CAS-2026-{uuid.uuid4().hex[:4].upper()}"

    incident = SOSIncident(
        incident_id=inc_id,
        user_id=req.user_id,
        user_name=req.user_name,
        phone=req.phone,
        trigger_type=req.trigger_type,
        severity=req.severity or "HIGH",
        notes=req.notes,
        status="ACTIVE_DISPATCH",
        latitude=req.location.latitude,
        longitude=req.location.longitude,
        accuracy_meters=req.location.accuracy_meters or 10.0,
        address=req.location.address or "Live GPS Geofence Alert",
        geofence_radius_km=5.0,
        case_id=case_id
    )
    db.add(incident)

    # Provision corresponding case and timeline record
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
        location=req.location.address or f"Lat {req.location.latitude:.4f}, Lng {req.location.longitude:.4f}",
        assigned_precinct="Central Police Precinct #01"
    )
    db.add(new_case)

    # Add initial timeline event
    initial_event = TimelineEvent(
        case_id=case_id,
        title=f"Incident Alert Broadcasted ({req.trigger_type})",
        description=f"Automated 5 km geofence dispatch triggered by {req.user_name}. Notes: {req.notes or 'None'}",
        actor_role="citizen",
        actor_name=req.user_name
    )
    db.add(initial_event)

    db.commit()
    db.refresh(incident)

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
def get_active_incidents(db: Session = Depends(get_db)):
    """
    Retrieve all active emergency SOS dispatches with live responder details.
    """
    incidents = db.query(SOSIncident).filter(
        SOSIncident.status == "ACTIVE_DISPATCH"
    ).order_by(SOSIncident.created_at.desc()).all()

    results = []
    
    """
    Retrieve all active emergency SOS dispatches with live responder details.
    """
    incidents = db.query(SOSIncident).filter(
        SOSIncident.status == "ACTIVE_DISPATCH"
    ).order_by(SOSIncident.created_at.desc()).all()

    results = []

    for inc in incidents:
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

        results.append({
            "incident_id": inc.incident_id,
            "user_id": inc.user_id,
            "user_name": inc.user_name,
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
            "active_responders": responders,
            "case_id": inc.case_id
        })

    return results

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

    # Check if already responded
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
    db: Session = Depends(get_db)
):
    """
    Mark an active incident as resolved and close the associated case timeline.
    """
    inc = db.query(SOSIncident).filter(SOSIncident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    inc.status = "RESOLVED"

    # Update linked case
    case = db.query(IncidentCase).filter(IncidentCase.case_id == inc.case_id).first()
    if case:
        case.status = "RESOLVED"
        timeline_evt = TimelineEvent(
            case_id=inc.case_id,
            title="Incident Resolved & Case Closed",
            description=f"Resolution logged by {resolved_by}. Notes: {notes}",
            actor_role="police",
            actor_name=resolved_by
        )
        db.add(timeline_evt)

    db.commit()
    return {"status": "success", "message": f"Incident {incident_id} marked as RESOLVED."}

"""
PERIMETER Platform - Notification & Real-Time Alert Engine
Handles role-based emergency alerts and WebSocket streaming for Police, Volunteers, Journalists, and Citizens.
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import json
import asyncio

from app.db.session import get_db, SessionLocal
from app.models.notification import Notification
from app.models.user import User
from app.core.security import get_current_user, get_optional_user

router = APIRouter(prefix="/notifications", tags=["Notifications & Real-Time Alerts"])

class ConnectionManager:
    def __init__(self):
        # Maps role -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {
            "police": [],
            "volunteer": [],
            "journalist": [],
            "user": [],
            "admin": []
        }

    async def connect(self, websocket: WebSocket, role: str):
        await websocket.accept()
        r = role.lower()
        if r not in self.active_connections:
            self.active_connections[r] = []
        self.active_connections[r].append(websocket)

    def disconnect(self, websocket: WebSocket, role: str):
        r = role.lower()
        if r in self.active_connections and websocket in self.active_connections[r]:
            self.active_connections[r].remove(websocket)

    async def broadcast_to_role(self, role: str, message: dict):
        r = role.lower()
        conns = self.active_connections.get(r, [])
        dead_conns = []
        for connection in conns:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_conns.append(connection)
        for dc in dead_conns:
            if dc in conns:
                conns.remove(dc)

    async def broadcast_emergency(self, police_payload: dict, volunteer_payload: dict, journalist_payload: dict):
        """Broadcast role-tailored payloads respecting privacy levels."""
        await self.broadcast_to_role("police", police_payload)
        await self.broadcast_to_role("admin", police_payload)
        await self.broadcast_to_role("volunteer", volunteer_payload)
        await self.broadcast_to_role("journalist", journalist_payload)

manager = ConnectionManager()

def dispatch_sos_notifications(
    db: Session,
    incident_id: str,
    user_name: str,
    phone: Optional[str],
    lat: float,
    lng: float,
    accuracy: float,
    address: str,
    severity: str,
    trigger_type: str,
    nearby_volunteers_count: int = 0
):
    """
    Creates persistent notification records in the database with strict role-based visibility.
    """
    now = datetime.utcnow()
    notifications_created = []

    # 1. POLICE NOTIFICATION: Full details, exact GPS, victim phone, immediate dispatch request
    pol_notif = Notification(
        target_role="police",
        incident_id=incident_id,
        title=f"🚨 CRITICAL SOS: {user_name}",
        message=f"Live distress alert ({trigger_type.replace('_', ' ')}). Location: {address}. Accuracy: ±{accuracy:.0f}m. Phone: {phone or 'Provided in profile'}. {nearby_volunteers_count} nearby volunteers alerted.",
        severity=severity or "CRITICAL",
        latitude=lat,
        longitude=lng,
        approximate_area=address,
        is_read=False,
        created_at=now
    )
    db.add(pol_notif)
    notifications_created.append(pol_notif)

    # 2. VOLUNTEER NOTIFICATION: Geofence dispatch, safe info, navigation ready
    vol_notif = Notification(
        target_role="volunteer",
        incident_id=incident_id,
        title=f"🚨 5km Emergency Alert: {trigger_type.replace('_', ' ')}",
        message=f"Distress beacon triggered near {address}. First responders requested. Accept to navigate to scene.",
        severity=severity or "HIGH",
        latitude=lat,
        longitude=lng,
        approximate_area=address,
        is_read=False,
        created_at=now
    )
    db.add(vol_notif)
    notifications_created.append(vol_notif)

    # 3. JOURNALIST NOTIFICATION: Public-safe, approximate neighborhood ONLY, NO private coordinates
    safe_area = address.split(",")[0] if "," in address else address
    prs_notif = Notification(
        target_role="journalist",
        incident_id=incident_id,
        title=f"📰 Verified Incident Reported: {incident_id}",
        message=f"Emergency case opened in {safe_area} sector. Priority: {severity}. Police dispatch active.",
        severity="INFO",
        latitude=None,  # Intentionally masked for victim privacy
        longitude=None,
        approximate_area=safe_area,
        is_read=False,
        created_at=now
    )
    db.add(prs_notif)
    notifications_created.append(prs_notif)

    db.commit()
    return notifications_created

@router.get("/")
def get_user_notifications(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve persistent notifications tailored to authenticated user's role and ID.
    Enforces role-based privacy filters.
    """
    query = db.query(Notification).filter(
        (Notification.target_role == current_user.role) |
        (Notification.target_role == "all") |
        (Notification.recipient_user_id == current_user.id)
    )

    if current_user.role == "admin":
        query = db.query(Notification)

    items = query.order_by(Notification.created_at.desc()).limit(limit).all()

    # Format response with privacy masks
    results = []
    for item in items:
        # If user is journalist or citizen and not emergency responder, mask exact coordinates
        show_coords = current_user.role in ["police", "volunteer", "admin"]
        results.append({
            "id": item.id,
            "incident_id": item.incident_id,
            "target_role": item.target_role,
            "title": item.title,
            "message": item.message,
            "severity": item.severity,
            "latitude": item.latitude if show_coords else None,
            "longitude": item.longitude if show_coords else None,
            "approximate_area": item.approximate_area,
            "is_read": item.is_read,
            "created_at": item.created_at
        })

    return results

@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.is_read = True
    db.commit()
    return {"status": "success", "id": notification_id}

@router.websocket("/ws/{role}")
async def websocket_alerts_endpoint(websocket: WebSocket, role: str):
    """
    Real-time WebSocket alerts channel for Police Command, Volunteers, and Press.
    """
    await manager.connect(websocket, role)
    try:
        # Send initial confirmation
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "role": role,
            "status": "LISTENING_FOR_EMERGENCY_DISPATCHES",
            "timestamp": datetime.utcnow().isoformat()
        }))
        while True:
            # Keep connection alive, listen for client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, role)
    except Exception:
        manager.disconnect(websocket, role)

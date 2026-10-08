"""
PERIMETER Platform - Real Geolocation Service API
Handles GPS coordinate ingestion, PostGIS spatial indexing, and privacy-filtered responder queries.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.user import User
from app.models.location import UserLocation
from app.schemas.location import LocationUpdateRequest, LocationResponse, ResponderLocationInfo
from app.core.security import get_current_user, require_role, get_optional_user
from app.db.spatial import haversine_distance_km, point_to_wkt

router = APIRouter(prefix="/location", tags=["Real Geolocation & PostGIS Service"])

@router.post("/update", response_model=LocationResponse)
def update_user_location(
    req: LocationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest user GPS coordinates. Sets current active position and records historical trail.
    Updates the user's last_active_at heartbeat.
    """
    # 1. Update user heartbeat
    current_user.last_active_at = datetime.utcnow()
    current_user.is_active = True

    # 2. Archive previous current locations for this user
    db.query(UserLocation).filter(
        UserLocation.user_id == current_user.id,
        UserLocation.is_current == True
    ).update({"is_current": False})

    # 3. Create new spatial location record
    loc = UserLocation(
        user_id=current_user.id,
        latitude=req.latitude,
        longitude=req.longitude,
        location_point=point_to_wkt(req.latitude, req.longitude),
        accuracy=req.accuracy or 10.0,
        timestamp=req.timestamp or datetime.utcnow(),
        source=req.source or "browser_gps",
        is_current=True,
        privacy_level=req.privacy_level or "EMERGENCY"
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)

    return loc

@router.get("/me", response_model=Optional[LocationResponse])
def get_my_current_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current authenticated user's latest recorded location.
    """
    loc = db.query(UserLocation).filter(
        UserLocation.user_id == current_user.id,
        UserLocation.is_current == True
    ).order_by(UserLocation.timestamp.desc()).first()

    if not loc:
        return None
    return loc

@router.get("/responders", response_model=List[ResponderLocationInfo])
def get_active_responders(
    current_user: User = Depends(require_role(["police", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Police Command & Admin: Retrieve real-time coordinates of active police and volunteers.
    Enforces RBAC: Ordinary citizens cannot query other users' exact GPS locations.
    """
    # Find current locations of users with role in ['police', 'volunteer']
    locations = db.query(UserLocation, User).join(
        User, UserLocation.user_id == User.id
    ).filter(
        UserLocation.is_current == True,
        User.role.in_(["police", "volunteer"])
    ).all()

    results = []
    for loc, u in locations:
        results.append(ResponderLocationInfo(
            user_id=u.id,
            name=u.name,
            role=u.role,
            badge_title=u.badge_title,
            latitude=loc.latitude,
            longitude=loc.longitude,
            last_updated=loc.timestamp,
            is_active=bool(u.is_active)
        ))
    return results

@router.get("/nearby-volunteers")
def get_nearby_volunteers(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(5.0, ge=0.5, le=50.0),
    current_user: User = Depends(require_role(["police", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Authoritative Spatial Proximity Query:
    Locate active, available volunteers within a specific radius (default 5 km).
    """
    active_vol_locations = db.query(UserLocation, User).join(
        User, UserLocation.user_id == User.id
    ).filter(
        UserLocation.is_current == True,
        User.role == "volunteer",
        User.is_active == True
    ).all()

    nearby = []
    for loc, u in active_vol_locations:
        dist = haversine_distance_km(lat, lng, loc.latitude, loc.longitude)
        if dist <= radius_km:
            nearby.append({
                "volunteer_id": u.id,
                "name": u.name,
                "badge": u.dynamic_field_1 or "VOL-VERIFIED",
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "distance_km": round(dist, 2),
                "accuracy_meters": loc.accuracy,
                "last_seen": loc.timestamp
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return {
        "center": {"latitude": lat, "longitude": lng},
        "radius_km": radius_km,
        "total_nearby": len(nearby),
        "volunteers": nearby
    }

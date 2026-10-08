"""
PERIMETER Platform - Geospatial & PostGIS Abstraction Layer
Supports native PostgreSQL + PostGIS spatial geometry and indexing,
with transparent mathematical spatial fallback for SQLite development.
"""
import math
from typing import Optional, Tuple, List
from sqlalchemy import Column, String, Float, func
from sqlalchemy.types import TypeDecorator
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement

class SpatialPoint(TypeDecorator):
    """
    Cross-database Spatial POINT Type.
    In PostgreSQL, creates a native PostGIS geometry(Point, 4326) column.
    In SQLite, stores WKT / lat-lng text representation cleanly without requiring mod_spatialite.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geometry(geometry_type="POINT", srid=4326, management=True))
        return dialect.type_descriptor(String(128))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, tuple) and len(value) == 2:
            lat, lng = value
            if dialect.name == "postgresql":
                return WKTElement(f"POINT({lng} {lat})", srid=4326)
            return f"POINT({lng} {lat})"
        if isinstance(value, str):
            if dialect.name == "postgresql" and not isinstance(value, WKTElement):
                return WKTElement(value, srid=4326)
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if hasattr(value, "data"):
            # GeoAlchemy2 WKBElement
            return str(value)
        return str(value)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) using Haversine formula.
    Result in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 99999.0

    # Earth radius in kilometers
    R = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def point_to_wkt(lat: float, lng: float) -> str:
    """Format decimal lat/lng to WKT POINT representation."""
    return f"POINT({lng} {lat})"


def parse_wkt_point(wkt_str: Optional[str]) -> Optional[Tuple[float, float]]:
    """Parse WKT POINT(lng lat) into (lat, lng) tuple."""
    if not wkt_str:
        return None
    try:
        clean = wkt_str.upper().replace("POINT", "").replace("(", "").replace(")", "").strip()
        parts = clean.split()
        if len(parts) >= 2:
            lng = float(parts[0])
            lat = float(parts[1])
            return (lat, lng)
    except Exception:
        pass
    return None

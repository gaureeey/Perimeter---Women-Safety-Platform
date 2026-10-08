"""
PERIMETER Platform - Database Inspection Utility
Inspects tables, records, users, SOS events, and locations in real-time.
Works seamlessly on both PostgreSQL + PostGIS and local SQLite databases.

Usage:
    python backend/scripts/inspect_db.py
    python backend/scripts/inspect_db.py --table users
    python backend/scripts/inspect_db.py --table sos
    python backend/scripts/inspect_db.py --table locations
    python backend/scripts/inspect_db.py --table crime
"""
import sys
import os
import argparse

# Set UTF-8 stdout encoding for Windows compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import engine, SessionLocal
from app.models.user import User
from app.models.sos import SOSIncident, Responder
from app.models.case import IncidentCase, TimelineEvent
from app.models.location import UserLocation
from app.models.notification import Notification
from app.models.crime import CrimeStatistic, AreaSafetyScore

def print_separator(char="=", length=80):
    print(char * length)

def inspect_summary(db):
    print("\n" + "=" * 80)
    print("🛡️  PERIMETER DATABASE INSPECTION REPORT")
    print(f"🔗 Database Dialect: {engine.dialect.name.upper()} ({engine.url.render_as_string(hide_password=True)})")
    print("=" * 80)

    counts = {
        "Users": db.query(User).count(),
        "Active Responders / Volunteers": db.query(User).filter(User.role.in_(["volunteer", "police"])).count(),
        "SOS Incidents": db.query(SOSIncident).count(),
        "Active SOS Emergencies": db.query(SOSIncident).filter(SOSIncident.status.in_(["ACTIVE_DISPATCH", "ACKNOWLEDGED"])).count(),
        "Universal Incident Cases": db.query(IncidentCase).count(),
        "Case Timeline Events": db.query(TimelineEvent).count(),
        "User Location Records": db.query(UserLocation).count(),
        "Dispatched Notifications": db.query(Notification).count(),
        "NCRB Crime Records (2021-2023)": db.query(CrimeStatistic).count(),
        "Calculated Area Safety Scores": db.query(AreaSafetyScore).count(),
    }

    for label, count in counts.items():
        print(f"  • {label:<35} : {count:>5} records")
    print("-" * 80)

def inspect_users(db, limit=10):
    print("\n👤 [USERS TABLE]")
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    if not users:
        print("  (No users found)")
        return

    header = f"{'ID':<14} | {'NAME':<20} | {'EMAIL':<26} | {'ROLE':<10} | {'STATUS':<8} | {'LAST ACTIVE'}"
    print(header)
    print("-" * len(header))
    for u in users:
        status = "Active" if getattr(u, 'is_active', True) else "Inactive"
        last_act = u.last_active_at.strftime("%Y-%m-%d %H:%M") if getattr(u, 'last_active_at', None) else "Never"
        print(f"{str(u.id)[:14]:<14} | {u.name[:20]:<20} | {u.email[:26]:<26} | {u.role:<10} | {status:<8} | {last_act}")

def inspect_sos(db, limit=10):
    print("\n🚨 [SOS INCIDENTS TABLE]")
    incidents = db.query(SOSIncident).order_by(SOSIncident.created_at.desc()).limit(limit).all()
    if not incidents:
        print("  (No SOS events recorded yet)")
        return

    header = f"{'INCIDENT ID':<16} | {'VICTIM NAME':<16} | {'TRIGGER':<14} | {'SEVERITY':<8} | {'STATUS':<15} | {'LAT/LNG'}"
    print(header)
    print("-" * len(header))
    for inc in incidents:
        coords = f"({inc.latitude:.4f}, {inc.longitude:.4f})"
        print(f"{inc.incident_id:<16} | {inc.user_name[:16]:<16} | {inc.trigger_type[:14]:<14} | {inc.severity:<8} | {inc.status:<15} | {coords}")

def inspect_locations(db, limit=10):
    print("\n📍 [USER LOCATIONS TABLE]")
    locs = db.query(UserLocation, User).join(User, UserLocation.user_id == User.id).order_by(UserLocation.timestamp.desc()).limit(limit).all()
    if not locs:
        print("  (No location records found)")
        return

    header = f"{'USER':<18} | {'ROLE':<10} | {'LATITUDE':<10} | {'LONGITUDE':<10} | {'ACCURACY':<8} | {'PRIVACY':<14} | {'CURRENT'}"
    print(header)
    print("-" * len(header))
    for loc, u in locs:
        is_curr = "Yes" if loc.is_current else "No"
        print(f"{u.name[:18]:<18} | {u.role:<10} | {loc.latitude:<10.4f} | {loc.longitude:<10.4f} | ±{loc.accuracy_meters:<6.1f}m | {loc.privacy_level:<14} | {is_curr}")

def inspect_crime_and_safety(db, limit=10):
    print("\n📊 [AREA SAFETY SCORES & NCRB BASELINE]")
    scores = db.query(AreaSafetyScore).order_by(AreaSafetyScore.last_calculated_at.desc()).limit(limit).all()
    if not scores:
        print("  (No Area Safety Scores generated)")
        return

    header = f"{'AREA NAME':<22} | {'RISK SCORE':<10} | {'RISK LEVEL':<12} | {'INCIDENTS':<10} | {'TREND':<12} | {'SOURCES'}"
    print(header)
    print("-" * len(header))
    for s in scores:
        print(f"{s.area_name[:22]:<22} | {s.risk_score:<10.1f} | {s.risk_level:<12} | {s.incident_count:<10} | {s.crime_trend:<12} | {s.data_sources}")

def main():
    parser = argparse.ArgumentParser(description="PERIMETER Database Inspector")
    parser.add_argument("--table", choices=["all", "users", "sos", "locations", "crime"], default="all", help="Target table to inspect")
    parser.add_argument("--limit", type=int, default=10, help="Max records to display per table")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        inspect_summary(db)
        if args.table in ["all", "users"]:
            inspect_users(db, args.limit)
        if args.table in ["all", "sos"]:
            inspect_sos(db, args.limit)
        if args.table in ["all", "locations"]:
            inspect_locations(db, args.limit)
        if args.table in ["all", "crime"]:
            inspect_crime_and_safety(db, args.limit)
        print("\n" + "=" * 80)
        print("✨ Database inspection completed successfully.")
        print("=" * 80 + "\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()

"""
PERIMETER Platform - PostgreSQL + PostGIS Setup & Migration Script
Initializes the database schema and enables PostGIS spatial extension.
"""
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sqlalchemy import text
from app.db.session import engine, Base
from app.core.config import settings
from app.db.init_db import init_db

def setup_database():
    print("=" * 60)
    print("🛡️  PERIMETER — Database & PostGIS Setup")
    print(f"🔗 Target Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print("=" * 60)

    # 1. Enable PostGIS extension if connected to PostgreSQL
    if "postgresql" in str(engine.url):
        try:
            print("🗺️  Enabling PostGIS extension on PostgreSQL...")
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
            print("✅ PostGIS spatial extension is ACTIVE!")
        except Exception as e:
            print(f"⚠️  Note on PostGIS extension: {e}")
    else:
        print("ℹ️  Running on SQLite with Haversine spatial math fallback.")

    # 2. Run table creation and seed check
    print("📦 Creating and verifying database tables...")
    init_db()
    print("✅ All tables created successfully!")
    print("\nTables in database:")
    from sqlalchemy import inspect
    insp = inspect(engine)
    for tbl in sorted(insp.get_table_names()):
        print(f"  - {tbl}")
    print("\n✅ Database setup complete and verified.")

if __name__ == "__main__":
    setup_database()

# 🛡️ PERIMETER — Women & Community Safety Platform

**PERIMETER** is an integrated community safety and emergency dispatch platform combining an Instagram-grade visual social network with an automated 5-tier spatial emergency response engine. It connects Citizens, Verified Volunteers, City Police Command, Credentialed Journalists, and Platform Administrators into a single transparent, role-governed safety ecosystem.

---

## 🚀 Quick Start Guide

### 1. Run the Entire Platform (Backend + Web Consoles)
To start both the FastAPI backend on port `8000` and the web frontend on port `8080`:
```bash
python run_platform.py
```
Then open your browser to: **`http://127.0.0.1:8080`**

### 2. Inspect Database Data (Users, SOS, Crime Stats, Risk Scores)
To inspect the relational database (works seamlessly with SQLite and PostgreSQL):
```bash
python inspect_db.py
```

### 3. Run Comprehensive Integration Tests
```bash
python backend/test_phase2_integration.py
```

---

## 👥 5-Tier Universal Role Matrix

Every authenticated persona in PERIMETER shares the **same core social features** (Profile, Bio, Feed, Device Media Posts, 24H Stories, Direct Messaging, Broadcast Channels, Likes/Comments/Shares, Follow System) with specialized operational dashboards according to backend RBAC.

| Role | Social Profile & Feed | Operational Dashboard | Primary Capabilities |
| :--- | :---: | :--- | :--- |
| **👩 Citizen User** | ✅ Yes (`user.html` / `profile.html`) | Safe Corridor & SOS Hub | Trigger SOS, real-time GPS tracking, safe route analysis, report incidents, community feed. |
| **🙋 Verified Volunteer** | ✅ Yes (`user.html` / `profile.html`) | `volunteer.html` | 5 km geofence distress radar, PostGIS proximity alerts, live navigation to incident, arrival check-in. |
| **🚔 City Police Command** | ✅ Yes (`user.html` / `profile.html`) | `police.html` | Tactical command map, full victim GPS & phone, patrol dispatch, timeline updates, case resolution. |
| **📰 Press Reporter** | ✅ Yes (`user.html` / `profile.html`) | `journalist.html` | Privacy-safe verified incident desk, case investigation notes, published articles linked to cases. |
| **⚙️ Super Administrator** | ✅ Yes (`user.html` / `profile.html`) | `admin.html` | System KPI metrics, user governance (activation/role), live SOS monitor, content moderation, DB audit. |

---

## 🗄️ Database Architecture & `perimeter.db` Clarification

### Database Engine Selection
1. **Local Development / Offline Mode (Zero Configuration):**
   - The platform automatically uses SQLite at `backend/perimeter.db`.
   - `perimeter.db` is a standard binary SQLite 3 database file. When opened in generic text editors, it displays as "binary or unsupported". Inspect it directly using `python inspect_db.py` or standard SQLite clients (`sqlite3 backend/perimeter.db`).
2. **Production Mode (Spatial PostGIS):**
   - Configure `DATABASE_URL=postgresql://user:password@host:5432/perimeter` in `.env`.
   - The backend uses SQLAlchemy ORM with PostGIS spatial geometry (`ST_DWithin`, `ST_Distance`) for high-throughput spatial querying.

---

## 📷 Device Media Upload Engine

PERIMETER supports direct media uploads from device storage, gallery, and camera:
- **Frontend:** `<input type="file" accept="image/*,video/*" multiple>` with carousel/grid preview and individual item removal (up to 10 items per post).
- **Backend (`/api/v1/media/upload`, `/api/v1/media/upload-multiple`):**
  - Enforces MIME type checking (`image/jpeg`, `image/png`, `image/webp`, `video/mp4`, `video/webm`).
  - Strict extension blacklist: executable scripts (`.exe`, `.bat`, `.php`, `.py`, `.sh`, `.js`) are rejected with `400 Bad Request`.
  - Configurable limits: Max 10 MB per image, Max 50 MB per video.
  - Sanitized UUID storage saved to `backend/uploads/` (never exposed directly to raw user filenames).

---

## 📍 Real GPS Geolocation & Location Privacy

1. **Zero Random Coordinates in Production:**
   - Real browser/device geolocation (`navigator.geolocation`) is used.
   - User consent is requested before live tracking (`[Allow Location]` / `[Not Now]`).
   - Live location status displays exact coordinates, accuracy readout (`± XX m`), and updated timestamp.
2. **Continuous Live SOS Tracking:**
   - When an SOS is triggered, initial GPS is locked and an `activeEmergencyBanner` is displayed.
   - While active, `LocationService.startEmergencyTracking` streams updated coordinates to `POST /api/v1/sos/{id}/location`.
   - Police command map updates in real time.
   - When resolved, tracking is terminated immediately.
3. **Role-Based Location Privacy:**
   - **Police & Admin:** Full victim GPS coordinates, street address, and phone number.
   - **Volunteers:** 5 km spatial proximity calculation and navigation waypoint.
   - **Journalists & Public:** Victim identity shielded; only high-level district/neighborhood area exposed.

---

## 🚶 Safe Route Risk Analysis

PERIMETER evaluates routes between origin and destination by breaking them into waypoints:
1. Samples coordinates along candidate routes.
2. Evaluates segment risk scores using Perimeter verified incidents and NCRB district baselines.
3. Displays side-by-side comparison:
   - **Fastest Route**
   - **Lower Reported Risk Route** (patrolled transit corridors)
4. *Important Note:* The platform transparently uses *"Lower reported risk based on available data"* rather than promising "guaranteed safety".

---

## 🗺️ Heatmap & NCRB Data Attribution

- **Perimeter Incidents:** Real active and historical platform distress beacons and community reports.
- **NCRB Statistics:** Official district-level statistics from the National Crime Records Bureau (*Crime in India*).
- *NCRB Limitation:* NCRB publishes aggregated administrative area data rather than exact crime coordinates. PERIMETER uses NCRB as an area-level baseline risk layer combined with precise incident GPS points.

---

## 🛡️ License & Credits
Built for community safety and emergency dispatch transparency.

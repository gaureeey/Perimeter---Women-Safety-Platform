# 🛡️ PERIMETER — Women Safety & Community Response Platform

PERIMETER is a community-driven women's safety platform that combines an Instagram-style visual feed with an automated 5-tier emergency dispatch system. It connects Citizens, Verified Volunteers, Credentialed Journalists, and Police into a single, transparent safety network.

---

## ✨ Key Features

* **📱 Social Safety Feed:** Share safety updates, stories, and location alerts with verified role badges (`Police Verified`, `Verified Reporter`, `Volunteer`).
* **🚨 Motion Shake SOS:** Hands-free emergency alert triggered by smartphone accelerometer data ($g$-force debouncing) alongside an in-app hold button.
* **👥 4-User Governance:** Role-based access control (RBAC) with tailored dashboards for Citizens, Volunteers, Journalists, and Police.
* **🗺️ Geospatial Safety Heatmaps:** Real-time incident density mapping with automatic geofence entry warnings for high-risk zones.
* **⚡ 5 km Geofenced Dispatch:** Asynchronous push notifications sent instantly to nearby verified responders.
* **📋 Universal Case Timeline:** Immutable incident logging that tracks every step from initial SOS trigger to police resolution.

---

## 👥 4-User Role Matrix

| User Role | Main Interface | Primary Capabilities |
| :--- | :--- | :--- |
| **👩 Citizen User** | Social Feed & SOS Dashboard | Trigger Shake SOS, share updates, view heatmaps, report vehicle accidents, track wellness logs. |
| **🙋 Verified Volunteer** | Emergency Dispatch Console | Receive 5 km radius alerts, accept dispatches, share live trajectories, log arrival times. |
| **📰 Verified Journalist** | Press Desk & Case Suite | Publish verified news reports, search archives, attach press updates directly to active case IDs. |
| **🚔 City Police** | Command & Control Console | Receive priority SOS alerts, dispatch patrol units, issue official notices, resolve and archive cases. |

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CLIENT LAYER                                                             │
│    • Native Android App (Java) — Citizen & Volunteer Mobile Interfaces       │
│    • Web Consoles (HTML5 / React.js) — Police & Journalist Consoles         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / REST API / JWT
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 2. API GATEWAY & SECURITY (Python FastAPI)                                  │
│    • OAuth2 / JWT Authentication • Role-Based Access Control (RBAC) Interceptor │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Async Requests
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 3. CORE SERVICES ENGINE                                                      │
│    • Motion Sensor Debouncer • Geofence Router (PostGIS ST_DWithin 5 km)     │
│    • Heatmap Aggregator     • Case Timeline & Audit Service                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Task Queue
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 4. DATA & REALTIME LAYER                                                    │
│    • PostgreSQL + PostGIS (Spatial Data & Schemas)                          │
│    • Redis + Celery (Async Push Dispatch Queue)                             │
│    • Firebase Cloud Messaging (FCM High-Priority Push Alerts)               │
└─────────────────────────────────────────────────────────────────────────────┘

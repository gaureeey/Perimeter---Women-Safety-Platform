# Admin SOS Route Fix v3

The Admin page was receiving 404 for `/admin/sos-overview`. The backend now exposes the audit route both under `/api/v1/admin/sos-overview` and the legacy `/admin/sos-overview` compatibility path.

IMPORTANT: stop any old Uvicorn process and start the backend from THIS extracted project folder.

```bat
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000/openapi.json` and search for `sos-overview`.

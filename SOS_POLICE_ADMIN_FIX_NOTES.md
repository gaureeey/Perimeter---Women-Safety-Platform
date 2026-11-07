# PERIMETER — Police/Admin SOS Fix

## What changed

1. Citizen SOS creates **three persistent records in SQLite**:
   - SOS incident (`sos_incidents`)
   - linked case (`cases`)
   - community feed post (`feed_posts`, tag `SOS_ALERT`)

2. Every SOS is broadcast through the backend WebSocket hub to:
   - Police Command
   - Verified Volunteers
   - Admin

3. Police and Admin dashboards also poll `/api/v1/sos/active` every 3 seconds, so they do not depend on WebSocket delivery.

4. WebSocket connections now use `127.0.0.1:8000` directly. This avoids the common `localhost` vs `127.0.0.1` mismatch when the frontend is opened from different browsers.

5. Police dashboard loads the SOS endpoint separately from the case endpoint. A failure in the case list no longer hides the SOS queue.

6. Police community feed displays the persistent `SOS_ALERT` post created by the citizen SOS.

7. Admin has a dedicated **Live Citizen SOS Alerts** panel.

## Correct startup

From the project root:

```text
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, serve the frontend:

```text
python serve.py
```

Then open the citizen and police/admin dashboards from the same frontend server, for example:

```text
http://localhost:8080/user.html
http://localhost:8080/police.html
http://localhost:8080/admin.html
```

## Test

1. Log in as Citizen in Chrome.
2. Log in as Police in Firefox.
3. Keep both pages open.
4. Press SOS in Citizen.
5. Police should show the active SOS in **Active Emergency Incident Queue** and receive a toast/browser notification.
6. Police **Community Safety Feed** should contain `🚨 SOS Alert` with the case ID.
7. Admin should show the SOS under **Live Citizen SOS Alerts**.
8. The same incident/case ID should be visible in all three places.

If the browser shows an older page after replacing the project, use Ctrl+Shift+R on each dashboard to bypass cached HTML/JS.

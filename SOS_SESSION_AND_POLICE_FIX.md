PERIMETER — FINAL SOS SESSION/POLICE FIX

IMPORTANT:
The frontend previously stored the JWT in localStorage. localStorage is shared by every tab/window of the same browser origin. If Citizen and Police were opened in two Firefox windows, logging into one persona could overwrite the other's token. This made /sos/active and the Police WebSocket authenticate as the wrong persona.

This build changes authentication to sessionStorage, which is isolated per browser tab. You can now use:
- Firefox Tab 1: Citizen
- Firefox Tab 2: Police
- Firefox Tab 3: Admin
Each tab keeps its own JWT/session.

It also changes the API/WebSocket host to use the current frontend hostname (localhost or 127.0.0.1), avoiding mixed-host configuration.

TEST:
1. Start backend from backend folder:
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
2. Start frontend from project root OR frontend folder:
   python -m http.server 8080 --directory frontend
   OR from project root: python serve.py
3. Open separate tabs.
4. Log in as Citizen in one tab and Police in another.
5. Hard refresh both tabs.
6. Citizen: select Immediate Danger and hold SOS for 2 seconds.
7. Police: active SOS should appear within about 1 second; community SOS post should also appear.
8. Admin: active SOS should appear similarly.

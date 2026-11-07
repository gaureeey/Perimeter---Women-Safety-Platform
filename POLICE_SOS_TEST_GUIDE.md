# PERIMETER-W Police SOS Test

## Start
1. Close every old `python`, `uvicorn`, and Perimeter server window first.
2. Double-click `START_PERIMETER_W.bat`.
3. Keep both command windows open.
4. Open Citizen, Police, Volunteer and Admin in separate browser tabs/windows.

## Test
1. Login Citizen.
2. Open SOS Radar.
3. Select `Immediate Danger` / HIGH (or CRITICAL).
4. Hold SOS for 2 seconds.
5. Police dashboard should update within about 2 seconds.
6. The Police Active Emergency Incident Queue should show:
   - LIVE SOS
   - citizen name
   - severity
   - Case ID
   - location
   - Dispatch Patrol
   - Resolve & Archive
7. Police should also see the same event in Community Safety Feed as an `SOS_ALERT`.
8. Volunteer/Admin should continue receiving their SOS updates.
9. Volunteer Accept should send the acceptance message back to the Citizen.
10. Police Resolve should close the linked SOS and case.

## Important
The police page now uses the friend's proven command-dashboard layout, but the live queue is wired to the newer Perimeter-W backend and session/auth API.

The backend also has a localhost-only compatibility fallback for `/api/v1/sos/active`, because older police dashboard clients sometimes poll without attaching the JWT. Production deployments should keep authenticated access enabled.

## If an old server is still running
Do NOT start another server on the same port. Close old command windows first.

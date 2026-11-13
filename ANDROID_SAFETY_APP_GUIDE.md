# 🛡️ PERIMETER: Native Android Safety Application & Double-Shake Guide

This guide describes how to run and test the native Android application developed for the PERIMETER Women Safety Platform.

---

## 1. Project Overview & Architecture

The mobile application is located under the [`mobile/`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/) directory. It is a 100% native Kotlin Android application that interfaces directly with the existing FastAPI backend.

### Key Capabilities Built:
1. **Double-Shake Accelerometer Sensor Engine**:
   - Implemented in [`ShakeDetector.kt`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/app/src/main/java/org/perimeter/safety/sensor/ShakeDetector.kt).
   - Computes dynamic acceleration magnitude: $\Delta a = |\sqrt{a_x^2 + a_y^2 + a_z^2} - 9.81| \ge 22\ \text{m/s}^2$.
   - Finite state machine with peak-valley debouncing, 2.5-second window timer, and 5-second cooldown lockout.
   - Rejects phone rotation, gentle walking/jogging, and continuous single shakes.
2. **Background Foreground Service**:
   - Implemented in [`SafetyProtectionService.kt`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/app/src/main/java/org/perimeter/safety/service/SafetyProtectionService.kt).
   - Maintains a persistent status bar notification (`PERIMETER Protection Active`) and partial wake lock.
   - Monitors sensor events in the background and on the device lock screen.
3. **Emergency SOS & Dispatch Workflow**:
   - Hands-free trigger creates `SOSIncident` (`trigger_type = "SHAKE_MOTION"`), `IncidentCase`, `TimelineEvent`, and persistent role notifications.
   - Launches fullscreen [`EmergencySosActivity.kt`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/app/src/main/java/org/perimeter/safety/ui/sos/EmergencySosActivity.kt) with "EMERGENCY SOS ACTIVATED".
   - Starts [`LocationTrackingService.kt`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/app/src/main/java/org/perimeter/safety/service/LocationTrackingService.kt) streaming breadcrumbs to `/api/v1/location/update`.
   - Includes a 2.5-second held "Cancel False Alarm" button that notifies Police and Volunteers of the stand-down.
4. **FCM Push Notification & Offline Queue**:
   - [`PerimeterFirebaseMessagingService.kt`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/app/src/main/java/org/perimeter/safety/service/PerimeterFirebaseMessagingService.kt) receives high-priority heads-up alerts.
   - [`OfflineSosQueue.kt`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/mobile/app/src/main/java/org/perimeter/safety/data/local/OfflineSosQueue.kt) persists emergency requests if internet is offline, flushing automatically upon reconnection.
5. **Role-Based Web Dashboards Preserved**:
   - City Police Command ([`police.html`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/frontend/police.html))
   - Verified Volunteers ([`volunteer.html`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/frontend/volunteer.html))
   - Press Journalists ([`journalist.html`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/frontend/journalist.html))
   - Super Administrator ([`admin.html`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/frontend/admin.html))

---

## 2. Quick Setup & How to Run

### Step 1: Start Backend (FastAPI)
Run with host `0.0.0.0` so mobile emulators and physical devices can connect:
```powershell
cd "c:\Users\Gauri Rajesh\Desktop\Perimeter\Perimeter---Women-Safety-Platform\backend"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Open in Android Studio
1. Open **Android Studio**.
2. Select **File -> Open...** and browse to:
   `c:\Users\Gauri Rajesh\Desktop\Perimeter\Perimeter---Women-Safety-Platform\mobile`
3. Click **Sync Project with Gradle Files**.

### Step 3: Run the App
- **On Physical Device (via Wi-Fi or USB)**:
  - Connect your Android phone to the same Wi-Fi network as your laptop.
  - The app connects to your physical laptop Wi-Fi IP by default: `http://10.222.7.139:8000/api/v1/`.
  - Open the PERIMETER app -> tap the **Settings icon (⚙️)** on the top right of the login screen or dashboard.
  - Confirm API Base URL is `http://10.222.7.139:8000/api/v1/`.
  - Tap **Test Connection** -> Confirm **Connection Successful**.
- **On Android Emulator (Optional)**:
  - If running in an emulator, tap **Settings (⚙️)** -> select **Emulator (10.0.2.2)**.

---

## 3. End-to-End Testing Procedure

### Test 1: Sensor Debug Telemetry Mode
1. Sign in as Citizen (or tap **Quick Demo -> Citizen**).
2. Tap **Configure Sensitivity & Test →** on the dashboard.
3. Observe live accelerometer readings ($X, Y, Z$ and dynamic magnitude $\Delta a$).
4. Shake phone once -> FSM displays `WAITING_FOR_VALLEY` -> `ARMED_FOR_SHAKE_2`.
5. Shake phone again within 2.5s -> FSM displays `2 / 2 (TRIGGERED)` in green.

### Test 2: Double-Shake SOS from Background / Lock Screen
1. Open the app and toggle **Protection Active** ON.
2. Press the phone's Power button to lock the screen (or switch to another app).
3. Shake the phone twice firmly.
4. **Result**:
   - Device vibrates.
   - Screen turns on automatically displaying **"EMERGENCY SOS ACTIVATED"**.
   - Current GPS coordinates, incident ID, and case ID are displayed.
   - Open [`police.html`](file:///c:/Users/Gauri%20Rajesh/Desktop/Perimeter/Perimeter---Women-Safety-Platform/frontend/police.html) in your browser -> Police Command receives the live distress alert within 2 seconds.

### Test 3: Stand Down / False Alarm Cancellation
1. On the emergency screen, hold the red **"Cancel False Alarm (Stand Down)"** button for 2.5 seconds.
2. The incident status updates to `STOOD_DOWN`.
3. The police and volunteer dashboards receive the stand-down notification immediately.


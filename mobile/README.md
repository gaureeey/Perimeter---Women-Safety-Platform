# 📱 PERIMETER — Native Android Safety Application

A production-grade, native Android safety application built with Kotlin, Jetpack, Android SensorManager, and Retrofit 2 that connects directly to the existing PERIMETER FastAPI backend.

---

## ✨ Features

- **🚨 Hands-Free Double-Shake SOS**: Built-in 3-axis accelerometer sensor detection. Users can shake their phone twice to trigger emergency dispatch without unlocking the phone or touching the screen.
- **🛡️ Background Safety Protection Service**: Android Foreground Service with persistent notification and partial wake lock, allowing continuous monitoring when the screen is turned off or while other apps are active.
- **⚡ 5-Tier Responder Dispatch**: Immediate notification to Police Command (`police.html`), verified volunteers within a 5 km geofence (`volunteer.html`), and press desks (`journalist.html`).
- **📍 Real-Time GPS Tracking**: Automatic continuous breadcrumb transmission to `/api/v1/location/update` every 10 seconds during an active emergency.
- **📴 Offline Resilience**: Emergency SOS is queued locally if the phone is temporarily offline and automatically flushed upon network restoration.
- **🛠️ Accelerometer Telemetry Debug Mode**: Live visualization meter for testing $X, Y, Z$ and dynamic magnitude $\Delta a$, with configurable sensitivity thresholds (Low, Medium, High) and window intervals (2.0s – 3.0s).
- **⚙️ Configurable API Base URL**: Defaults directly to your physical laptop Wi-Fi address (`http://10.222.7.139:8000/api/v1/`), with quick switching to Android Studio Emulator (`http://10.0.2.2:8000/api/v1/`).

---

## 🏗️ Architecture & Package Structure

```text
mobile/
├── app/
│   ├── build.gradle.kts
│   ├── proguard-rules.pro
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/org/perimeter/safety/
│       │   ├── PerimeterApplication.kt
│       │   ├── data/
│       │   │   ├── api/
│       │   │   │   ├── ApiService.kt             # Retrofit 2 endpoints
│       │   │   │   ├── AuthInterceptor.kt        # Bearer JWT injector
│       │   │   │   └── NetworkClient.kt          # Dynamic base URL client
│       │   │   ├── local/
│       │   │   │   ├── AppPreferences.kt         # Secure persistent preferences
│       │   │   │   └── OfflineSosQueue.kt        # Resilient offline retry queue
│       │   │   └── model/                        # DTOs (Auth, SOS, Location, Notif)
│       │   ├── sensor/
│       │   │   ├── ShakeDetector.kt              # Double-shake peak/valley FSM
│       │   │   └── ShakeSensitivity.kt           # Sensitivity thresholds
│       │   ├── service/
│       │   │   ├── SafetyProtectionService.kt    # Foreground motion monitoring
│       │   │   ├── LocationTrackingService.kt    # Emergency GPS tracker
│       │   │   └── PerimeterFirebaseMessagingService.kt  # FCM push receiver
│       │   └── ui/
│       │       ├── auth/                         # Splash, Login, Register
│       │       ├── dashboard/                    # Citizen Home Dashboard
│       │       ├── protection/                   # Sensor debug & sensitivity
│       │       ├── sos/                          # Fullscreen Alarm & Tracking
│       │       ├── history/                      # SOS Incident History
│       │       ├── notifications/                # Role Notification Centre
│       │       └── profile/                      # Settings & API URL Switcher
│       └── res/ (layouts, drawables, values, colors)
├── build.gradle.kts
├── settings.gradle.kts
└── gradlew.bat
```

---

## 🚀 How to Open & Run in Android Studio

1. **Launch Android Studio**.
2. Select **File -> Open...** and choose the `Perimeter---Women-Safety-Platform/mobile` directory.
3. Allow Gradle to sync dependencies.
4. Start your local FastAPI backend:
   ```powershell
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Run the app on an **Android Virtual Device (AVD)** or physical smartphone connected via USB / Wi-Fi debugging.

### Configuring Base URL:
- **Physical Device**: Uses `http://10.222.7.139:8000/api/v1/` by default.
- **Android Emulator**: In **Settings (Gear Icon) -> API Base URL**, tap **Emulator (10.0.2.2)**.

---

## 🧪 Testing the Double-Shake SOS

### 1. In the App:
1. Sign in as Citizen (or tap **Quick Demo -> Citizen**).
2. Tap the **Protection Active** toggle switch. The persistent notification will appear in the Android status bar.
3. Navigate to **Configure Sensitivity & Test →**.
4. Shake the phone twice:
   - Notice the live dynamic magnitude $\Delta a$ meter spike above the threshold ($22\ \text{m/s}^2$).
   - The FSM will transition `IDLE -> WAITING_FOR_VALLEY -> ARMED_FOR_SHAKE_2 -> TRIGGERED`.
5. When outside the debug screen or on the lock screen, shaking twice triggers the emergency workflow:
   - Device vibrates.
   - GPS coordinates are captured.
   - `POST /api/v1/sos/trigger` is sent to the backend with `trigger_type = "SHAKE_MOTION"`.
   - The fullscreen **EMERGENCY SOS ACTIVATED** alarm screen opens.
   - Police Command (`police.html`) and Volunteers (`volunteer.html`) receive the dispatch immediately.


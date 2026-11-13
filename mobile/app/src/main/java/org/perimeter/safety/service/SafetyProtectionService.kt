package org.perimeter.safety.service

import android.annotation.SuppressLint
import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import org.perimeter.safety.PerimeterApplication
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.local.OfflineSosQueue
import org.perimeter.safety.data.model.LocationCoords
import org.perimeter.safety.data.model.SOSTriggerRequest
import org.perimeter.safety.sensor.ShakeDetector
import org.perimeter.safety.sensor.ShakeSensitivity
import org.perimeter.safety.ui.dashboard.MainActivity
import org.perimeter.safety.ui.sos.EmergencySosActivity

class SafetyProtectionService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private lateinit var shakeDetector: ShakeDetector
    private var wakeLock: PowerManager.WakeLock? = null
    private val prefs by lazy { AppPreferences(this) }
    private val offlineQueue by lazy { OfflineSosQueue(this) }

    override fun onCreate() {
        super.onCreate()
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        val sensitivity = ShakeSensitivity.fromString(prefs.shakeSensitivity)
        val windowMs = prefs.shakeWindowMs

        shakeDetector = ShakeDetector(
            sensitivity = sensitivity,
            windowMs = windowMs,
            onDoubleShakeDetected = { handleDoubleShakeTrigger() }
        )

        acquireWakeLock()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action ?: ACTION_START_PROTECTION

        if (action == ACTION_STOP_PROTECTION) {
            stopProtection()
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, buildForegroundNotification())
        registerSensorListener()
        prefs.isProtectionActive = true

        return START_STICKY
    }

    private fun registerSensorListener() {
        if (accelerometer != null) {
            val registered = sensorManager.registerListener(
                shakeDetector,
                accelerometer,
                SensorManager.SENSOR_DELAY_GAME
            )
            Log.i(TAG, "Shake sensor registered with SENSOR_DELAY_GAME: $registered")
        } else {
            Log.e(TAG, "No accelerometer hardware found on this device.")
        }
    }

    private fun unregisterSensorListener() {
        sensorManager.unregisterListener(shakeDetector)
    }

    @SuppressLint("WakelockTimeout")
    private fun acquireWakeLock() {
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "PERIMETER:SafetyProtectionWakeLock"
        ).apply {
            setReferenceCounted(false)
            acquire(12 * 60 * 60 * 1000L) // Safety cap: 12 hours
        }
    }

    private fun releaseWakeLock() {
        try {
            if (wakeLock?.isHeld == true) {
                wakeLock?.release()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error releasing wakelock: ${e.message}")
        }
    }

    private fun vibrateAlert() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                val vibrator = vibratorManager.defaultVibrator
                vibrator.vibrate(VibrationEffect.createWaveform(longArrayOf(0, 300, 150, 400), -1))
            } else {
                @Suppress("DEPRECATION")
                val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createWaveform(longArrayOf(0, 300, 150, 400), -1))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(longArrayOf(0, 300, 150, 400), -1)
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Could not vibrate: ${e.message}")
        }
    }

    private fun handleDoubleShakeTrigger() {
        vibrateAlert()
        Log.w(TAG, "🚨 Motion Sensor detected DOUBLE-SHAKE! Dispatching Emergency SOS...")

        serviceScope.launch {
            val user = prefs.currentUser
            val userName = user?.name ?: "Citizen"
            val userId = user?.id
            val phone = user?.phone

            // Obtain current GPS coordinates
            val fusedClient = LocationServices.getFusedLocationProviderClient(this@SafetyProtectionService)
            var latitude = 19.0760
            var longitude = 72.8777
            var accuracy = 10.0f
            var address = user?.location ?: "Live Geolocation Coordinates"

            if (ContextCompat.checkSelfPermission(this@SafetyProtectionService, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
                ContextCompat.checkSelfPermission(this@SafetyProtectionService, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
            ) {
                try {
                    val locationResult = fusedClient.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, null)
                    val location = locationResult.await()
                    if (location != null) {
                        latitude = location.latitude
                        longitude = location.longitude
                        accuracy = location.accuracy
                        address = "Lat: ${"%.4f".format(latitude)}, Lng: ${"%.4f".format(longitude)}"
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Location capture failed, using fallback coordinates: ${e.message}")
                }
            } else {
                Log.w(TAG, "Location permission unavailable; using fallback coordinates.")
            }

            val sosRequest = SOSTriggerRequest(
                userName = userName,
                userId = userId,
                phone = phone,
                triggerType = "SHAKE_MOTION",
                severity = "CRITICAL",
                location = LocationCoords(
                    latitude = latitude,
                    longitude = longitude,
                    accuracyMeters = accuracy,
                    address = address
                ),
                notes = "Hands-free emergency triggered by Double-Shake gesture."
            )

            // Submit to Backend or Enqueue if offline
            var incidentId = "SOS-${System.currentTimeMillis()}"
            var caseId = "CAS-${System.currentTimeMillis()}"
            var status = "ACTIVE_DISPATCH"

            try {
                val apiService = NetworkClient.getApiService(prefs)
                val response = apiService.triggerSos(sosRequest)
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    incidentId = body.incidentId
                    caseId = body.caseId
                    status = body.status
                    prefs.lastIncidentId = incidentId
                    Log.i(TAG, "SOS created on backend: Incident=$incidentId, Case=$caseId")
                } else {
                    Log.w(TAG, "Backend returned error ${response.code()}. Enqueueing offline.")
                    offlineQueue.enqueue(sosRequest)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Network failure during SOS dispatch. Enqueueing offline: ${e.message}")
                offlineQueue.enqueue(sosRequest)
            }

            // Launch continuous tracking service
            LocationTrackingService.startTracking(this@SafetyProtectionService, incidentId)

            // Open Fullscreen Emergency Screen (Works even if phone is locked)
            val emergencyIntent = Intent(this@SafetyProtectionService, EmergencySosActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                putExtra(EmergencySosActivity.EXTRA_INCIDENT_ID, incidentId)
                putExtra(EmergencySosActivity.EXTRA_CASE_ID, caseId)
                putExtra(EmergencySosActivity.EXTRA_STATUS, status)
                putExtra(EmergencySosActivity.EXTRA_LAT, latitude)
                putExtra(EmergencySosActivity.EXTRA_LNG, longitude)
                putExtra(EmergencySosActivity.EXTRA_ADDRESS, address)
                putExtra(EmergencySosActivity.EXTRA_TRIGGER_TYPE, "SHAKE_MOTION")
            }
            startActivity(emergencyIntent)
        }
    }

    private fun buildForegroundNotification(): Notification {
        val openAppIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val openAppPendingIntent = PendingIntent.getActivity(
            this, 0, openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, SafetyProtectionService::class.java).apply {
            action = ACTION_STOP_PROTECTION
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 1, stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, PerimeterApplication.CHANNEL_PROTECTION)
            .setSmallIcon(R.drawable.ic_shield_check)
            .setContentTitle(getString(R.string.protection_active))
            .setContentText(getString(R.string.protection_subtitle_active))
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(openAppPendingIntent)
            .addAction(
                R.drawable.ic_stop,
                getString(R.string.action_stop_protection),
                stopPendingIntent
            )
            .build()
    }

    private fun stopProtection() {
        prefs.isProtectionActive = false
        unregisterSensorListener()
        releaseWakeLock()
    }

    override fun onDestroy() {
        stopProtection()
        serviceScope.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        private const val TAG = "SafetyProtectionService"
        private const val NOTIFICATION_ID = 2001
        const val ACTION_START_PROTECTION = "org.perimeter.safety.ACTION_START_PROTECTION"
        const val ACTION_STOP_PROTECTION = "org.perimeter.safety.ACTION_STOP_PROTECTION"

        fun startProtection(context: Context) {
            val intent = Intent(context, SafetyProtectionService::class.java).apply {
                action = ACTION_START_PROTECTION
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stopProtection(context: Context) {
            val intent = Intent(context, SafetyProtectionService::class.java).apply {
                action = ACTION_STOP_PROTECTION
            }
            context.startService(intent)
        }
    }
}


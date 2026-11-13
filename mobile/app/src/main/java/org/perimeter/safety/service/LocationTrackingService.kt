package org.perimeter.safety.service

import android.annotation.SuppressLint
import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.android.gms.location.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import org.perimeter.safety.PerimeterApplication
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.model.LocationUpdateRequest
import org.perimeter.safety.ui.sos.EmergencySosActivity

class LocationTrackingService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private lateinit var locationCallback: LocationCallback
    private val prefs by lazy { AppPreferences(this) }
    private var activeIncidentId: String? = null

    override fun onCreate() {
        super.onCreate()
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        locationCallback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                val loc = result.lastLocation ?: return
                Log.d(TAG, "Live SOS Location breadcrumb: ${loc.latitude}, ${loc.longitude} (±${loc.accuracy}m)")

                serviceScope.launch {
                    try {
                        val apiService = NetworkClient.getApiService(prefs)
                        val req = LocationUpdateRequest(
                            latitude = loc.latitude,
                            longitude = loc.longitude,
                            accuracy = loc.accuracy,
                            source = "mobile_gps_emergency",
                            privacyLevel = "EMERGENCY"
                        )
                        apiService.updateLocation(req)
                    } catch (e: Exception) {
                        Log.w(TAG, "Failed to stream emergency breadcrumb: ${e.message}")
                    }
                }
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        activeIncidentId = intent?.getStringExtra(EXTRA_INCIDENT_ID) ?: prefs.lastIncidentId

        startForeground(NOTIFICATION_ID, buildTrackingNotification())
        startLocationUpdates()

        return START_STICKY
    }

    @SuppressLint("MissingPermission")
    private fun startLocationUpdates() {
        val locationRequest = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 10000L).apply {
            setMinUpdateIntervalMillis(5000L)
            setMinUpdateDistanceMeters(5.0f)
            setWaitForAccurateLocation(false)
        }.build()

        try {
            fusedLocationClient.requestLocationUpdates(
                locationRequest,
                locationCallback,
                Looper.getMainLooper()
            )
            Log.i(TAG, "Continuous emergency GPS tracking initiated.")
        } catch (e: Exception) {
            Log.e(TAG, "Could not start location updates: ${e.message}")
        }
    }

    private fun stopLocationUpdates() {
        try {
            fusedLocationClient.removeLocationUpdates(locationCallback)
        } catch (e: Exception) {
            Log.w(TAG, "Error removing location updates: ${e.message}")
        }
    }

    private fun buildTrackingNotification(): Notification {
        val intent = Intent(this, EmergencySosActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, PerimeterApplication.CHANNEL_EMERGENCY)
            .setSmallIcon(R.drawable.ic_sos_alert)
            .setContentTitle("🚨 EMERGENCY SOS BROADCASTING")
            .setContentText("Streaming live GPS coordinates to Police Command & Responders")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setOngoing(true)
            .setContentIntent(pendingIntent)
            .build()
    }

    override fun onDestroy() {
        stopLocationUpdates()
        serviceScope.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        private const val TAG = "LocationTrackingService"
        private const val NOTIFICATION_ID = 2002
        private const val EXTRA_INCIDENT_ID = "extra_incident_id"

        fun startTracking(context: Context, incidentId: String?) {
            val intent = Intent(context, LocationTrackingService::class.java).apply {
                putExtra(EXTRA_INCIDENT_ID, incidentId)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stopTracking(context: Context) {
            val intent = Intent(context, LocationTrackingService::class.java)
            context.stopService(intent)
        }
    }
}


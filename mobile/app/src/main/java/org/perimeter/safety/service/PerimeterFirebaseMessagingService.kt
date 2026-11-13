package org.perimeter.safety.service

import android.app.PendingIntent
import android.content.Intent
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.perimeter.safety.PerimeterApplication
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.model.DeviceTokenRegisterRequest
import org.perimeter.safety.ui.notifications.NotificationCenterActivity
import org.perimeter.safety.ui.sos.EmergencySosActivity

class PerimeterFirebaseMessagingService : FirebaseMessagingService() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val prefs by lazy { AppPreferences(this) }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.i(TAG, "Refreshed FCM Device Registration Token: $token")
        prefs.fcmToken = token

        // If user is currently authenticated, update backend registration immediately
        if (prefs.isLoggedIn) {
            serviceScope.launch {
                try {
                    val api = NetworkClient.getApiService(prefs)
                    val req = DeviceTokenRegisterRequest(
                        token = token,
                        platform = "android",
                        deviceName = android.os.Build.MODEL
                    )
                    api.registerDeviceToken(req)
                    Log.i(TAG, "Synced refreshed FCM device token to backend successfully.")
                } catch (e: Exception) {
                    Log.w(TAG, "Failed to sync refreshed FCM token: ${e.message}")
                }
            }
        }
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
        Log.i(TAG, "Received FCM Push from: ${remoteMessage.from}")

        val data = remoteMessage.data
        val title = remoteMessage.notification?.title
            ?: data["title"]
            ?: getString(R.string.title_emergency_sos)

        val body = remoteMessage.notification?.body
            ?: data["body"]
            ?: "High priority safety alert received."

        val incidentId = data["incident_id"]
        val type = data["type"] ?: "ALERT"

        showNotification(title, body, incidentId, type)
    }

    private fun showNotification(title: String, body: String, incidentId: String?, type: String) {
        val targetIntent = if (incidentId != null && type.contains("EMERGENCY")) {
            Intent(this, EmergencySosActivity::class.java).apply {
                putExtra(EmergencySosActivity.EXTRA_INCIDENT_ID, incidentId)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
        } else {
            Intent(this, NotificationCenterActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            System.currentTimeMillis().toInt(),
            targetIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, PerimeterApplication.CHANNEL_EMERGENCY)
            .setSmallIcon(R.drawable.ic_sos_alert)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setVibrate(longArrayOf(0, 500, 200, 500, 200, 500))
            .build()

        try {
            NotificationManagerCompat.from(this).notify(System.currentTimeMillis().toInt(), notification)
        } catch (e: SecurityException) {
            Log.w(TAG, "Permission POST_NOTIFICATIONS missing: ${e.message}")
        }
    }

    companion object {
        private const val TAG = "PerimeterFCM"
    }
}


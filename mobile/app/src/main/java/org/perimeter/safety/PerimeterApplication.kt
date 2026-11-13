package org.perimeter.safety

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.os.Build

class PerimeterApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        instance = this
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            // 1. High Priority Emergency Alarm Channel
            val emergencySound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            val audioAttributes = AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .setUsage(AudioAttributes.USAGE_ALARM)
                .build()

            val emergencyChannel = NotificationChannel(
                CHANNEL_EMERGENCY,
                getString(R.string.channel_emergency_name),
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = getString(R.string.channel_emergency_desc)
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 500, 200, 500, 200, 500)
                setSound(emergencySound, audioAttributes)
                lockscreenVisibility = android.app.Notification.VISIBILITY_PUBLIC
            }

            // 2. Persistent Protection Service Channel (Foreground Service)
            val protectionChannel = NotificationChannel(
                CHANNEL_PROTECTION,
                getString(R.string.channel_protection_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.channel_protection_desc)
                setShowBadge(false)
            }

            notificationManager.createNotificationChannel(emergencyChannel)
            notificationManager.createNotificationChannel(protectionChannel)
        }
    }

    companion object {
        lateinit var instance: PerimeterApplication
            private set

        const val CHANNEL_EMERGENCY = "perimeter_emergency_channel"
        const val CHANNEL_PROTECTION = "perimeter_protection_channel"
    }
}


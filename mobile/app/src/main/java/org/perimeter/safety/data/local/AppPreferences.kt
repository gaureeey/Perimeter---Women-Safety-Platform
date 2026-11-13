package org.perimeter.safety.data.local

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import org.perimeter.safety.PerimeterApplication
import org.perimeter.safety.data.model.UserProfile

class AppPreferences(context: Context = PerimeterApplication.instance) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    private val gson = Gson()

    var authToken: String?
        get() = prefs.getString(KEY_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_TOKEN, value).apply()

    var currentUser: UserProfile?
        get() {
            val json = prefs.getString(KEY_USER, null) ?: return null
            return try {
                gson.fromJson(json, UserProfile::class.java)
            } catch (e: Exception) {
                null
            }
        }
        set(value) {
            val json = if (value != null) gson.toJson(value) else null
            prefs.edit().putString(KEY_USER, json).apply()
        }

    /**
     * Configurable API Base URL.
     * Default for Physical Device on Wi-Fi: http://10.222.7.139:8000/api/v1/
     * Android Studio Emulator: http://10.0.2.2:8000/api/v1/
     */
    var apiBaseUrl: String
        get() {
            val saved = prefs.getString(KEY_BASE_URL, null)
            // Automatically upgrade empty value or legacy emulator 10.0.2.2 to physical device URL
            if (saved.isNullOrBlank() || saved.contains("10.0.2.2")) {
                prefs.edit().putString(KEY_BASE_URL, DEFAULT_BASE_URL).apply()
                return DEFAULT_BASE_URL
            }
            return saved
        }
        set(value) {
            var url = value.trim()
            if (!url.endsWith("/")) url += "/"
            if (!url.contains("/api/v1/")) {
                url = if (url.endsWith("/")) "${url}api/v1/" else "$url/api/v1/"
            }
            prefs.edit().putString(KEY_BASE_URL, url).apply()
        }

    var isProtectionActive: Boolean
        get() = prefs.getBoolean(KEY_PROTECTION_ACTIVE, false)
        set(value) = prefs.edit().putBoolean(KEY_PROTECTION_ACTIVE, value).apply()

    var shakeSensitivity: String
        get() = prefs.getString(KEY_SHAKE_SENSITIVITY, "MEDIUM") ?: "MEDIUM"
        set(value) = prefs.edit().putString(KEY_SHAKE_SENSITIVITY, value).apply()

    var shakeWindowMs: Long
        get() = prefs.getLong(KEY_SHAKE_WINDOW, 2500L)
        set(value) = prefs.edit().putLong(KEY_SHAKE_WINDOW, value).apply()

    var fcmToken: String?
        get() = prefs.getString(KEY_FCM_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_FCM_TOKEN, value).apply()

    var lastIncidentId: String?
        get() = prefs.getString(KEY_LAST_INCIDENT, null)
        set(value) = prefs.edit().putString(KEY_LAST_INCIDENT, value).apply()

    val isLoggedIn: Boolean
        get() = !authToken.isNullOrBlank() && currentUser != null

    fun clearSession() {
        prefs.edit()
            .remove(KEY_TOKEN)
            .remove(KEY_USER)
            .remove(KEY_LAST_INCIDENT)
            .putBoolean(KEY_PROTECTION_ACTIVE, false)
            .apply()
    }

    companion object {
        private const val PREF_NAME = "perimeter_secure_prefs"
        private const val KEY_TOKEN = "jwt_token"
        private const val KEY_USER = "current_user_profile"
        private const val KEY_BASE_URL = "api_base_url"
        private const val KEY_PROTECTION_ACTIVE = "protection_active"
        private const val KEY_SHAKE_SENSITIVITY = "shake_sensitivity"
        private const val KEY_SHAKE_WINDOW = "shake_window_ms"
        private const val KEY_FCM_TOKEN = "fcm_device_token"
        private const val KEY_LAST_INCIDENT = "last_incident_id"

        const val DEFAULT_BASE_URL = "http://10.222.7.139:8000/api/v1/"
        const val EMULATOR_BASE_URL = "http://10.0.2.2:8000/api/v1/"
    }
}


package org.perimeter.safety.data.model

import com.google.gson.annotations.SerializedName
import java.io.Serializable

data class LocationUpdateRequest(
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("accuracy") val accuracy: Float = 10.0f,
    @SerializedName("source") val source: String = "mobile_gps",
    @SerializedName("privacy_level") val privacyLevel: String = "EMERGENCY"
)

data class LocationResponse(
    @SerializedName("id") val id: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("accuracy") val accuracy: Float,
    @SerializedName("timestamp") val timestamp: String,
    @SerializedName("is_current") val isCurrent: Boolean
)

data class DeviceTokenRegisterRequest(
    @SerializedName("token") val token: String,
    @SerializedName("platform") val platform: String = "android",
    @SerializedName("device_name") val deviceName: String? = null
)

data class DeviceTokenResponse(
    @SerializedName("status") val status: String,
    @SerializedName("token") val token: String,
    @SerializedName("platform") val platform: String,
    @SerializedName("message") val message: String
)

data class NotificationItem(
    @SerializedName("id") val id: String,
    @SerializedName("incident_id") val incidentId: String?,
    @SerializedName("target_role") val targetRole: String,
    @SerializedName("title") val title: String,
    @SerializedName("message") val message: String,
    @SerializedName("severity") val severity: String,
    @SerializedName("latitude") val latitude: Double?,
    @SerializedName("longitude") val longitude: Double?,
    @SerializedName("approximate_area") val approximateArea: String?,
    @SerializedName("is_read") val isRead: Boolean,
    @SerializedName("created_at") val createdAt: String
) : Serializable


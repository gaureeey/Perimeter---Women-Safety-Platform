package org.perimeter.safety.data.model

import com.google.gson.annotations.SerializedName
import java.io.Serializable

data class LocationCoords(
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("accuracy_meters") val accuracyMeters: Float? = 10.0f,
    @SerializedName("address") val address: String? = "Live Geolocation Coordinates"
) : Serializable

data class SOSTriggerRequest(
    @SerializedName("user_name") val userName: String,
    @SerializedName("user_id") val userId: String? = null,
    @SerializedName("phone") val phone: String? = null,
    @SerializedName("trigger_type") val triggerType: String = "SHAKE_MOTION",
    @SerializedName("severity") val severity: String = "CRITICAL",
    @SerializedName("location") val location: LocationCoords,
    @SerializedName("battery_percentage") val batteryPercentage: Int? = 85,
    @SerializedName("notes") val notes: String? = "Emergency triggered via Double-Shake gesture.",
    @SerializedName("category") val category: String = "public",
    @SerializedName("share_location") val shareLocation: Boolean = true,
    @SerializedName("record_audio") val recordAudio: Boolean = false,
    @SerializedName("silent_mode") val silentMode: Boolean = false
) : Serializable

data class ResponderInfo(
    @SerializedName("responder_id") val responderId: String,
    @SerializedName("responder_name") val responderName: String,
    @SerializedName("role") val role: String,
    @SerializedName("eta_minutes") val etaMinutes: Float,
    @SerializedName("distance_km") val distanceKm: Float,
    @SerializedName("status") val status: String
) : Serializable

data class SOSIncidentResponse(
    @SerializedName("incident_id") val incidentId: String,
    @SerializedName("user_id") val userId: String?,
    @SerializedName("user_name") val userName: String,
    @SerializedName("trigger_type") val triggerType: String,
    @SerializedName("severity") val severity: String?,
    @SerializedName("notes") val notes: String?,
    @SerializedName("status") val status: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("location") val location: LocationCoords,
    @SerializedName("geofence_radius_km") val geofenceRadiusKm: Float = 5.0f,
    @SerializedName("case_id") val caseId: String,
    @SerializedName("active_responders") val activeResponders: List<ResponderInfo> = emptyList(),
    @SerializedName("dispatch_role") val dispatchRole: String? = "both",
    @SerializedName("routing_reason") val routingReason: String? = null
) : Serializable

data class StandDownResponse(
    @SerializedName("status") val status: String,
    @SerializedName("message") val message: String
)


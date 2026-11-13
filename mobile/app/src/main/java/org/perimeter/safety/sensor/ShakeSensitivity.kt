package org.perimeter.safety.sensor

enum class ShakeSensitivity(val threshold: Float, val valleyThreshold: Float) {
    LOW(28.0f, 14.0f),      // Forceful deliberate shakes only
    MEDIUM(22.0f, 12.0f),   // Recommended balance for walking/night commutes
    HIGH(16.0f, 10.0f);     // Sensitive (suitable for pocket/bag movement)

    companion object {
        fun fromString(name: String?): ShakeSensitivity {
            return try {
                if (name != null) valueOf(name.uppercase()) else MEDIUM
            } catch (e: Exception) {
                MEDIUM
            }
        }
    }
}


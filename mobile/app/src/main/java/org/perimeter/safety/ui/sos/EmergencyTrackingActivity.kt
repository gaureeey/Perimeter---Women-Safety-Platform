package org.perimeter.safety.ui.sos

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.databinding.ActivityEmergencyTrackingBinding

class EmergencyTrackingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityEmergencyTrackingBinding
    private val prefs by lazy { AppPreferences(this) }
    private var incidentId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityEmergencyTrackingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        incidentId = intent.getStringExtra(EmergencySosActivity.EXTRA_INCIDENT_ID) ?: prefs.lastIncidentId
        val lat = intent.getDoubleExtra(EmergencySosActivity.EXTRA_LAT, 19.0760)
        val lng = intent.getDoubleExtra(EmergencySosActivity.EXTRA_LNG, 72.8777)

        binding.tvLiveCoords.text = "Lat: ${"%.4f".format(lat)}, Lng: ${"%.4f".format(lng)} (±8m accuracy)"
        binding.btnBack.setOnClickListener { finish() }

        startPollingResponders()
    }

    private fun startPollingResponders() {
        val id = incidentId ?: return

        lifecycleScope.launch {
            while (isActive) {
                try {
                    val api = NetworkClient.getApiService(prefs)
                    val response = api.getIncident(id)
                    if (response.isSuccessful && response.body() != null) {
                        val inc = response.body()!!
                        binding.tvLastPingTime.text = "Status: ${inc.status} • Updated just now"

                        val responders = inc.activeResponders
                        if (responders.isNotEmpty()) {
                            binding.layoutRespondersList.removeAllViews()
                            for (r in responders) {
                                val tv = TextView(this@EmergencyTrackingActivity).apply {
                                    text = "🏃 ${r.responderName} (${r.role.uppercase()})\n   ETA: ${r.etaMinutes} mins  •  Dist: ${r.distanceKm} km  •  Status: ${r.status}"
                                    setTextColor(ContextCompat.getColor(this@EmergencyTrackingActivity, R.color.status_safe))
                                    textSize = 13f
                                    setPadding(0, 8, 0, 8)
                                }
                                binding.layoutRespondersList.addView(tv)
                            }
                        }
                    }
                } catch (e: Exception) {
                    // Ignore transient network poll blips
                }
                delay(6000)
            }
        }
    }
}


package org.perimeter.safety.ui.sos

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.databinding.ActivityEmergencySosBinding
import org.perimeter.safety.service.LocationTrackingService
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class EmergencySosActivity : AppCompatActivity() {

    private lateinit var binding: ActivityEmergencySosBinding
    private val prefs by lazy { AppPreferences(this) }

    private var incidentId: String = ""
    private var caseId: String = ""
    private var status: String = "ACTIVE_DISPATCH"
    private var latitude: Double = 19.0760
    private var longitude: Double = 72.8777
    private var address: String = "Bandra West, Mumbai"
    private var triggerType: String = "SHAKE_MOTION"

    private var standDownJob: Job? = null
    private var standDownStartTime = 0L
    private val standDownDurationMs = 2500L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        configureLockScreenFlags()
        binding = ActivityEmergencySosBinding.inflate(layoutInflater)
        setContentView(binding.root)

        parseIntentData()
        setupUI()
        setupListeners()
    }

    private fun configureLockScreenFlags() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            )
        }
    }

    private fun parseIntentData() {
        incidentId = intent.getStringExtra(EXTRA_INCIDENT_ID) ?: prefs.lastIncidentId ?: "SOS-PENDING"
        caseId = intent.getStringExtra(EXTRA_CASE_ID) ?: "CAS-PENDING"
        status = intent.getStringExtra(EXTRA_STATUS) ?: "ACTIVE_DISPATCH"
        latitude = intent.getDoubleExtra(EXTRA_LAT, 19.0760)
        longitude = intent.getDoubleExtra(EXTRA_LNG, 72.8777)
        address = intent.getStringExtra(EXTRA_ADDRESS) ?: "Live GPS Location"
        triggerType = intent.getStringExtra(EXTRA_TRIGGER_TYPE) ?: "SHAKE_MOTION"
    }

    private fun setupUI() {
        binding.tvIncidentId.text = incidentId
        binding.tvCaseId.text = caseId
        binding.tvSosStatus.text = status
        binding.tvSosLocation.text = "$address (Lat: ${"%.4f".format(latitude)}, Lng: ${"%.4f".format(longitude)})"

        val sdf = SimpleDateFormat("dd MMM, hh:mm:ss a", Locale.getDefault())
        binding.tvSosTime.text = "Triggered at: ${sdf.format(Date())}"

        if (triggerType == "SHAKE_MOTION") {
            binding.tvTriggerBadge.text = "⚡ TRIGGERED VIA DOUBLE-SHAKE SENSOR GESTURE"
        } else {
            binding.tvTriggerBadge.text = "⚡ TRIGGERED VIA IN-APP SOS HOLD BUTTON"
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupListeners() {
        binding.btnViewTracking.setOnClickListener {
            val intent = Intent(this, EmergencyTrackingActivity::class.java).apply {
                putExtra(EXTRA_INCIDENT_ID, incidentId)
                putExtra(EXTRA_CASE_ID, caseId)
                putExtra(EXTRA_LAT, latitude)
                putExtra(EXTRA_LNG, longitude)
            }
            startActivity(intent)
        }

        // Cancel / Stand Down Button (Requires 2.5s hold to prevent accidental tap)
        binding.btnCancelAlarm.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startStandDownTimer()
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    cancelStandDownTimer()
                    true
                }
                else -> false
            }
        }
    }

    private fun startStandDownTimer() {
        standDownStartTime = System.currentTimeMillis()
        binding.pbStandDown.visibility = View.VISIBLE
        binding.pbStandDown.progress = 0

        standDownJob = lifecycleScope.launch {
            while (true) {
                val elapsed = System.currentTimeMillis() - standDownStartTime
                val progress = ((elapsed.toFloat() / standDownDurationMs) * 100).toInt()
                binding.pbStandDown.progress = progress

                if (elapsed >= standDownDurationMs) {
                    performStandDown()
                    break
                }
                delay(30)
            }
        }
    }

    private fun cancelStandDownTimer() {
        standDownJob?.cancel()
        standDownJob = null
        binding.pbStandDown.visibility = View.GONE
        binding.pbStandDown.progress = 0
    }

    private fun performStandDown() {
        cancelStandDownTimer()
        Toast.makeText(this, "Cancelling emergency alert...", Toast.LENGTH_SHORT).show()

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.standDownIncident(incidentId, "user_false_alarm_stand_down")
                if (response.isSuccessful) {
                    Toast.makeText(this@EmergencySosActivity, "✅ SOS Stood Down. Responders notified that you are safe.", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@EmergencySosActivity, "Stood down locally. Status updated.", Toast.LENGTH_SHORT).show()
            }

            // Stop continuous emergency GPS broadcast
            LocationTrackingService.stopTracking(this@EmergencySosActivity)
            finish()
        }
    }

    companion object {
        const val EXTRA_INCIDENT_ID = "extra_incident_id"
        const val EXTRA_CASE_ID = "extra_case_id"
        const val EXTRA_STATUS = "extra_status"
        const val EXTRA_LAT = "extra_lat"
        const val EXTRA_LNG = "extra_lng"
        const val EXTRA_ADDRESS = "extra_address"
        const val EXTRA_TRIGGER_TYPE = "extra_trigger_type"
    }
}


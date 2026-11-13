package org.perimeter.safety.ui.protection

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import org.perimeter.safety.R
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.databinding.ActivityMotionProtectionBinding
import org.perimeter.safety.sensor.ShakeDetector
import org.perimeter.safety.sensor.ShakeSensitivity
import org.perimeter.safety.service.SafetyProtectionService

class MotionProtectionActivity : AppCompatActivity(), ShakeDetector.ShakeDebugListener {

    private lateinit var binding: ActivityMotionProtectionBinding
    private val prefs by lazy { AppPreferences(this) }
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private var testShakeDetector: ShakeDetector? = null

    private var selectedSensitivity = ShakeSensitivity.MEDIUM
    private var selectedIntervalMs = 2500L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMotionProtectionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        loadCurrentConfig()
        setupListeners()
    }

    override fun onResume() {
        super.onResume()
        startDebugSensor()
    }

    override fun onPause() {
        stopDebugSensor()
        super.onPause()
    }

    private fun loadCurrentConfig() {
        selectedSensitivity = ShakeSensitivity.fromString(prefs.shakeSensitivity)
        selectedIntervalMs = prefs.shakeWindowMs

        when (selectedSensitivity) {
            ShakeSensitivity.LOW -> binding.toggleSensitivity.check(R.id.btnSensLow)
            ShakeSensitivity.MEDIUM -> binding.toggleSensitivity.check(R.id.btnSensMed)
            ShakeSensitivity.HIGH -> binding.toggleSensitivity.check(R.id.btnSensHigh)
        }

        when (selectedIntervalMs) {
            2000L -> binding.toggleInterval.check(R.id.btnInt20)
            2500L -> binding.toggleInterval.check(R.id.btnInt25)
            3000L -> binding.toggleInterval.check(R.id.btnInt30)
            else -> binding.toggleInterval.check(R.id.btnInt25)
        }

        binding.switchProtectionDetailed.isChecked = prefs.isProtectionActive
    }

    private fun setupListeners() {
        binding.switchProtectionDetailed.setOnCheckedChangeListener { _, isChecked ->
            if (isChecked) {
                SafetyProtectionService.startProtection(this)
                prefs.isProtectionActive = true
                Toast.makeText(this, "Protection Active", Toast.LENGTH_SHORT).show()
            } else {
                SafetyProtectionService.stopProtection(this)
                prefs.isProtectionActive = false
                Toast.makeText(this, "Protection Stopped", Toast.LENGTH_SHORT).show()
            }
        }

        binding.toggleSensitivity.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (!isChecked) return@addOnButtonCheckedListener
            selectedSensitivity = when (checkedId) {
                R.id.btnSensLow -> ShakeSensitivity.LOW
                R.id.btnSensHigh -> ShakeSensitivity.HIGH
                else -> ShakeSensitivity.MEDIUM
            }
            testShakeDetector?.updateConfig(selectedSensitivity, selectedIntervalMs)
        }

        binding.toggleInterval.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (!isChecked) return@addOnButtonCheckedListener
            selectedIntervalMs = when (checkedId) {
                R.id.btnInt20 -> 2000L
                R.id.btnInt30 -> 3000L
                else -> 2500L
            }
            testShakeDetector?.updateConfig(selectedSensitivity, selectedIntervalMs)
        }

        binding.btnSaveSettings.setOnClickListener {
            prefs.shakeSensitivity = selectedSensitivity.name
            prefs.shakeWindowMs = selectedIntervalMs

            // If service is running, restart it with new config
            if (prefs.isProtectionActive) {
                SafetyProtectionService.stopProtection(this)
                SafetyProtectionService.startProtection(this)
            }

            Toast.makeText(this, "Sensitivity saved (${selectedSensitivity.name}, ${selectedIntervalMs / 1000.0}s window)", Toast.LENGTH_SHORT).show()
            finish()
        }
    }

    private fun startDebugSensor() {
        if (accelerometer != null) {
            testShakeDetector = ShakeDetector(
                sensitivity = selectedSensitivity,
                windowMs = selectedIntervalMs,
                onDoubleShakeDetected = {
                    runOnUiThread {
                        Toast.makeText(this, "✅ Double-Shake Successfully Triggered in Test Mode!", Toast.LENGTH_LONG).show()
                        binding.tvShakesCount.text = "2 / 2 (TRIGGERED)"
                        binding.tvShakesCount.setTextColor(ContextCompat.getColor(this, R.color.status_safe))
                    }
                }
            ).apply {
                debugListener = this@MotionProtectionActivity
            }

            sensorManager.registerListener(testShakeDetector, accelerometer, SensorManager.SENSOR_DELAY_UI)
        }
    }

    private fun stopDebugSensor() {
        testShakeDetector?.let {
            sensorManager.unregisterListener(it)
        }
        testShakeDetector = null
    }

    override fun onSensorChanged(
        x: Float,
        y: Float,
        z: Float,
        magnitude: Float,
        deltaA: Float,
        stateName: String,
        shakeCount: Int
    ) {
        runOnUiThread {
            binding.tvFsmState.text = stateName
            binding.tvDeltaA.text = "${"%.1f".format(deltaA)} m/s² (Thresh: ${selectedSensitivity.threshold})"
            binding.pbAcceleration.progress = deltaA.toInt().coerceIn(0, 40)
            binding.tvRawValues.text = "X: ${"%.2f".format(x)}  |  Y: ${"%.2f".format(y)}  |  Z: ${"%.2f".format(z)} m/s²"

            if (shakeCount == 2) {
                binding.tvShakesCount.text = "2 / 2 (TRIGGERED)"
                binding.tvShakesCount.setTextColor(ContextCompat.getColor(this, R.color.status_safe))
            } else if (shakeCount == 1) {
                binding.tvShakesCount.text = "1 / 2 (Shake again!)"
                binding.tvShakesCount.setTextColor(ContextCompat.getColor(this, R.color.status_warning))
            } else {
                binding.tvShakesCount.text = "0 / 2"
                binding.tvShakesCount.setTextColor(ContextCompat.getColor(this, R.color.text_secondary))
            }
        }
    }
}


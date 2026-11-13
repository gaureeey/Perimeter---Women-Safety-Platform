package org.perimeter.safety.sensor

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.util.Log
import kotlin.math.abs
import kotlin.math.sqrt

class ShakeDetector(
    private var sensitivity: ShakeSensitivity = ShakeSensitivity.MEDIUM,
    private var windowMs: Long = 2500L,
    private val onDoubleShakeDetected: () -> Unit
) : SensorEventListener {

    private enum class State {
        IDLE,
        WAITING_FOR_VALLEY,
        ARMED_FOR_SHAKE_2,
        COOLDOWN
    }

    private var currentState: State = State.IDLE
    private var firstShakeTime: Long = 0L
    private var lastTriggerTime: Long = 0L
    private val cooldownMs: Long = 5000L

    interface ShakeDebugListener {
        fun onSensorChanged(
            x: Float,
            y: Float,
            z: Float,
            magnitude: Float,
            deltaA: Float,
            stateName: String,
            shakeCount: Int
        )
    }

    var debugListener: ShakeDebugListener? = null
    private var detectedShakesCount: Int = 0

    fun updateConfig(newSensitivity: ShakeSensitivity, newWindowMs: Long) {
        this.sensitivity = newSensitivity
        this.windowMs = newWindowMs
        reset()
    }

    fun reset() {
        currentState = State.IDLE
        firstShakeTime = 0L
        detectedShakesCount = 0
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null || event.sensor.type != Sensor.TYPE_ACCELEROMETER) return

        val x = event.values[0]
        val y = event.values[1]
        val z = event.values[2]

        // 1. Calculate 3-axis magnitude
        val magnitude = sqrt((x * x + y * y + z * z).toDouble()).toFloat()

        // 2. Subtract Earth's gravitational acceleration (9.81 m/s^2)
        val deltaA = abs(magnitude - SensorManagerGravityCompensation)

        val now = System.currentTimeMillis()

        // Handle Cooldown expiration
        if (currentState == State.COOLDOWN) {
            if (now - lastTriggerTime > cooldownMs) {
                currentState = State.IDLE
                detectedShakesCount = 0
            }
        }

        // Handle Window Timeout: if Shake 1 was detected but Shake 2 didn't arrive within windowMs
        if ((currentState == State.WAITING_FOR_VALLEY || currentState == State.ARMED_FOR_SHAKE_2) &&
            (now - firstShakeTime > windowMs)
        ) {
            Log.d(TAG, "Double-shake window expired (> ${windowMs}ms). Resetting to IDLE.")
            currentState = State.IDLE
            detectedShakesCount = 0
        }

        // Double-Shake Finite State Machine
        when (currentState) {
            State.IDLE -> {
                if (deltaA >= sensitivity.threshold) {
                    firstShakeTime = now
                    currentState = State.WAITING_FOR_VALLEY
                    detectedShakesCount = 1
                    Log.i(TAG, "Shake 1/2 detected! DeltaA=$deltaA >= ${sensitivity.threshold}. Arming debounce.")
                }
            }

            State.WAITING_FOR_VALLEY -> {
                // To avoid treating a single continuous long shake as two shakes,
                // the device must drop below the rest/valley threshold.
                if (deltaA <= sensitivity.valleyThreshold) {
                    currentState = State.ARMED_FOR_SHAKE_2
                    Log.d(TAG, "Valley detected (DeltaA=$deltaA <= ${sensitivity.valleyThreshold}). Armed for Shake 2.")
                }
            }

            State.ARMED_FOR_SHAKE_2 -> {
                if (deltaA >= sensitivity.threshold) {
                    val duration = now - firstShakeTime
                    Log.w(TAG, "⚡ DOUBLE-SHAKE CONFIRMED! Two shakes in ${duration}ms. Triggering SOS!")
                    detectedShakesCount = 2
                    currentState = State.COOLDOWN
                    lastTriggerTime = now
                    onDoubleShakeDetected()
                }
            }

            State.COOLDOWN -> {
                // Ignore sensor events during cooldown
            }
        }

        debugListener?.onSensorChanged(
            x = x,
            y = y,
            z = z,
            magnitude = magnitude,
            deltaA = deltaA,
            stateName = currentState.name,
            shakeCount = detectedShakesCount
        )
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // Not used for accelerometer thresholding
    }

    companion object {
        private const val TAG = "ShakeDetector"
        private const val SensorManagerGravityCompensation = 9.81f
    }
}


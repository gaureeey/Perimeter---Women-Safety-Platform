package org.perimeter.safety.ui.profile

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.databinding.ActivityProfileSettingsBinding
import org.perimeter.safety.service.SafetyProtectionService
import org.perimeter.safety.ui.auth.LoginActivity

class ProfileSettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProfileSettingsBinding
    private val prefs by lazy { AppPreferences(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProfileSettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        loadProfile()
        setupListeners()
    }

    private fun loadProfile() {
        val user = prefs.currentUser
        binding.tvProfileName.text = user?.name ?: "Citizen User"
        binding.tvProfileRole.text = "${user?.badgeTitle ?: "Citizen User"} • ${user?.username ?: ""}"
        binding.tvProfileEmail.text = "Email: ${user?.email ?: "Not provided"}"
        binding.tvProfilePhone.text = "Phone: ${user?.phone ?: "Not provided"}"
        binding.tvEmergencyContact.text = "Emergency Contact: ${user?.dynamicField1 ?: user?.phone ?: "Not set"}"

        binding.etBaseUrl.setText(prefs.apiBaseUrl)
    }

    private fun setupListeners() {
        binding.btnResetDefaultUrl.setOnClickListener {
            binding.etBaseUrl.setText(AppPreferences.DEFAULT_BASE_URL)
        }

        binding.btnSetEmulatorUrl.setOnClickListener {
            binding.etBaseUrl.setText(AppPreferences.EMULATOR_BASE_URL)
        }

        binding.btnSaveBaseUrl.setOnClickListener {
            val newUrl = binding.etBaseUrl.text.toString().trim()
            if (newUrl.isNotEmpty()) {
                prefs.apiBaseUrl = newUrl
                NetworkClient.resetClient()
                Toast.makeText(this, "API Base URL updated: ${prefs.apiBaseUrl}", Toast.LENGTH_SHORT).show()
            }
        }

        binding.btnTestConnection.setOnClickListener {
            val url = binding.etBaseUrl.text.toString().trim()
            prefs.apiBaseUrl = url
            NetworkClient.resetClient()

            lifecycleScope.launch {
                try {
                    val api = NetworkClient.getApiService(prefs)
                    val res = api.getCurrentUser()
                    if (res.isSuccessful) {
                        Toast.makeText(this@ProfileSettingsActivity, "✅ Connection Successful! Verified user: ${res.body()?.name}", Toast.LENGTH_LONG).show()
                    } else {
                        Toast.makeText(this@ProfileSettingsActivity, "Server responded with code ${res.code()}", Toast.LENGTH_LONG).show()
                    }
                } catch (e: Exception) {
                    Toast.makeText(this@ProfileSettingsActivity, "❌ Connection failed: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }

        binding.btnLogout.setOnClickListener {
            SafetyProtectionService.stopProtection(this)
            prefs.clearSession()
            NetworkClient.resetClient()

            Toast.makeText(this, "Signed out successfully", Toast.LENGTH_SHORT).show()
            val intent = Intent(this, LoginActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            }
            startActivity(intent)
            finish()
        }
    }
}


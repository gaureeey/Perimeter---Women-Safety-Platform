package org.perimeter.safety.ui.auth

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.model.DeviceTokenRegisterRequest
import org.perimeter.safety.data.model.UserLoginRequest
import org.perimeter.safety.databinding.ActivityLoginBinding
import org.perimeter.safety.ui.dashboard.MainActivity
import org.perimeter.safety.ui.profile.ProfileSettingsActivity

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private val prefs by lazy { AppPreferences(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupListeners()
    }

    override fun onResume() {
        super.onResume()
        binding.tvServerIndicator.text = "Server: ${prefs.apiBaseUrl}"
    }

    private fun setupListeners() {
        binding.btnServerSettings.setOnClickListener {
            startActivity(Intent(this, ProfileSettingsActivity::class.java))
        }

        binding.btnLogin.setOnClickListener {
            val identity = binding.etIdentity.text.toString().trim()
            val password = binding.etPassword.text.toString()

            if (identity.isEmpty()) {
                binding.tilIdentity.error = "Please enter your email or badge ID"
                return@setOnClickListener
            }
            if (password.isEmpty()) {
                binding.tilPassword.error = "Please enter your password"
                return@setOnClickListener
            }

            performLogin(identity, password)
        }

        binding.tvRegister.setOnClickListener {
            startActivity(Intent(this, RegisterActivity::class.java))
        }

        // Quick demo fillers
        binding.btnQuickCitizen.setOnClickListener {
            binding.etIdentity.setText("aarohi.sharma@perimeter.org")
            binding.etPassword.setText("password123")
        }
        binding.btnQuickVolunteer.setOnClickListener {
            binding.etIdentity.setText("priya.deshmukh@volunteers.perimeter.org")
            binding.etPassword.setText("password123")
        }
        binding.btnQuickPolice.setOnClickListener {
            binding.etIdentity.setText("patil.k@police.gov.in")
            binding.etPassword.setText("password123")
        }
    }

    private fun performLogin(identity: String, pass: String) {
        binding.progressBar.visibility = View.VISIBLE
        binding.btnLogin.isEnabled = false

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.login(UserLoginRequest(identity, pass))

                if (response.isSuccessful && response.body() != null) {
                    val tokenRes = response.body()!!
                    prefs.authToken = tokenRes.accessToken
                    prefs.currentUser = tokenRes.user

                    // Register FCM token if already obtained
                    prefs.fcmToken?.let { token ->
                        try {
                            api.registerDeviceToken(DeviceTokenRegisterRequest(token, "android", android.os.Build.MODEL))
                        } catch (e: Exception) {
                            // Non-critical background sync
                        }
                    }

                    Toast.makeText(this@LoginActivity, "Welcome back, ${tokenRes.user.name}!", Toast.LENGTH_SHORT).show()
                    startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                    finish()
                } else {
                    val errorMsg = response.errorBody()?.string() ?: "Invalid login credentials."
                    Toast.makeText(this@LoginActivity, "Login failed: $errorMsg", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@LoginActivity, "Connection error: ${e.message}\nMake sure backend is running on ${prefs.apiBaseUrl}", Toast.LENGTH_LONG).show()
            } finally {
                binding.progressBar.visibility = View.GONE
                binding.btnLogin.isEnabled = true
            }
        }
    }
}


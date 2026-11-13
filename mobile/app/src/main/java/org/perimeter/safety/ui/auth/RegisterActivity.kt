package org.perimeter.safety.ui.auth

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.model.UserRegisterRequest
import org.perimeter.safety.databinding.ActivityRegisterBinding
import org.perimeter.safety.ui.dashboard.MainActivity

class RegisterActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRegisterBinding
    private val prefs by lazy { AppPreferences(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupListeners()
    }

    private fun setupListeners() {
        binding.tvBackToLogin.setOnClickListener { finish() }

        binding.btnRegister.setOnClickListener {
            val name = binding.etName.text.toString().trim()
            val email = binding.etEmail.text.toString().trim()
            val phone = binding.etPhone.text.toString().trim()
            val emContact = binding.etEmergencyContact.text.toString().trim()
            val loc = binding.etLocation.text.toString().trim()
            val pass = binding.etPassword.text.toString()

            if (name.isEmpty() || email.isEmpty() || phone.isEmpty() || pass.isEmpty()) {
                Toast.makeText(this, "Please fill in all required fields", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            performRegister(name, email, phone, emContact, loc, pass)
        }
    }

    private fun performRegister(name: String, email: String, phone: String, emContact: String, loc: String, pass: String) {
        binding.progressBar.visibility = View.VISIBLE
        binding.btnRegister.isEnabled = false

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val req = UserRegisterRequest(
                    name = name,
                    email = email,
                    phone = phone,
                    password = pass,
                    role = "user",
                    dynamicField1 = emContact.ifEmpty { "+91 98000 00000" },
                    dynamicField2 = loc.ifEmpty { "Mumbai Metro Area" },
                    location = loc.ifEmpty { "Mumbai Metro Area" }
                )

                val response = api.register(req)
                if (response.isSuccessful && response.body() != null) {
                    val tokenRes = response.body()!!
                    prefs.authToken = tokenRes.accessToken
                    prefs.currentUser = tokenRes.user

                    Toast.makeText(this@RegisterActivity, "Account created successfully!", Toast.LENGTH_SHORT).show()
                    val intent = Intent(this@RegisterActivity, MainActivity::class.java).apply {
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                    }
                    startActivity(intent)
                    finish()
                } else {
                    val error = response.errorBody()?.string() ?: "Registration failed."
                    Toast.makeText(this@RegisterActivity, "Error: $error", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@RegisterActivity, "Network error: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                binding.progressBar.visibility = View.GONE
                binding.btnRegister.isEnabled = true
            }
        }
    }
}


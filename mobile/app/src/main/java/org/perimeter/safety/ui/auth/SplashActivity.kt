package org.perimeter.safety.ui.auth

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.ui.dashboard.MainActivity

@SuppressLint("CustomSplashScreen")
class SplashActivity : AppCompatActivity() {

    private val prefs by lazy { AppPreferences(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_splash)

        lifecycleScope.launch {
            delay(1200) // Brief animated branding pause

            if (prefs.isLoggedIn) {
                // Verify session with backend in background
                try {
                    val api = NetworkClient.getApiService(prefs)
                    val response = api.getCurrentUser()
                    if (response.isSuccessful && response.body() != null) {
                        prefs.currentUser = response.body()
                    }
                } catch (e: Exception) {
                    // Use cached session if network is momentarily unavailable
                }
                startActivity(Intent(this@SplashActivity, MainActivity::class.java))
            } else {
                startActivity(Intent(this@SplashActivity, LoginActivity::class.java))
            }
            finish()
        }
    }
}


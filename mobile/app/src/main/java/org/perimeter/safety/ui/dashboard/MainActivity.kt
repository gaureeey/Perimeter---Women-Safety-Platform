package org.perimeter.safety.ui.dashboard

import android.Manifest
import android.annotation.SuppressLint
import android.app.Dialog
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.local.OfflineSosQueue
import org.perimeter.safety.data.model.*
import org.perimeter.safety.databinding.ActivityMainBinding
import org.perimeter.safety.databinding.DialogStoryViewerBinding
import org.perimeter.safety.service.LocationTrackingService
import org.perimeter.safety.service.SafetyProtectionService
import org.perimeter.safety.ui.auth.LoginActivity
import org.perimeter.safety.ui.feed.FeedPostsAdapter
import org.perimeter.safety.ui.feed.StoriesAdapter
import org.perimeter.safety.ui.history.SosHistoryActivity
import org.perimeter.safety.ui.notifications.NotificationCenterActivity
import org.perimeter.safety.ui.profile.ProfileSettingsActivity
import org.perimeter.safety.ui.protection.MotionProtectionActivity
import org.perimeter.safety.ui.sos.EmergencySosActivity

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val prefs by lazy { AppPreferences(this) }
    private val offlineQueue by lazy { OfflineSosQueue(this) }
    private val fusedLocationClient by lazy { LocationServices.getFusedLocationProviderClient(this) }

    private lateinit var storiesAdapter: StoriesAdapter
    private lateinit var feedPostsAdapter: FeedPostsAdapter
    private var currentCategory = "ALL"

    private var holdJob: Job? = null
    private var holdStartTime = 0L
    private val holdDurationMs = 2000L

    private var attachedPostMediaUrl: String? = null
    private var attachedStoryMediaUrl: String? = null

    private var currentRadarLat = 19.0760
    private var currentRadarLng = 72.8777

    private val pickPostImageLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { uploadPostImageFromUri(it) }
    }

    private val pickStoryImageLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { uploadStoryImageFromUri(it) }
    }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val locationGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true
        if (locationGranted) {
            refreshLocation()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        requestPermissions()
        setupUI()
        setupBottomNav()
        setupFeedAndStories()
        setupRadarSection()
        setupListeners()
        loadFeedData()
        flushOfflineQueueIfAny()
    }

    override fun onResume() {
        super.onResume()
        updateProtectionStateUI()
        refreshLocation()
    }

    private fun requestPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        permissionLauncher.launch(permissions.toTypedArray())
    }

    private fun setupUI() {
        val user = prefs.currentUser
        val initials = user?.avatar ?: user?.name?.take(2)?.uppercase() ?: "AS"

        // Top Header
        binding.tvHeaderSubtitle.text = "Safety Social Hub • For You"

        // Feed Tab
        binding.tvCreatePostAvatar.text = initials

        // Setup Category Tag Spinner in Create Post Card
        val tags = listOf(
            "COMMUNITY_UPDATE",
            "SAFE_ROUTE",
            "HAZARD_ALERT",
            "HELP_REQUEST",
            "POLICE_NOTICE"
        )
        val spinnerAdapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_dropdown_item,
            tags.map { "#${it.replace('_', ' ')}" }
        )
        binding.spinnerPostTag.adapter = spinnerAdapter

        // SOS Tab
        binding.tvWelcomeUser.text = "Hi, ${user?.name ?: "Citizen"}"
        binding.tvRoleBadge.text = "${user?.badgeTitle ?: "Citizen User"} • ${user?.location ?: "Mumbai Area"}"

        // Profile Tab
        binding.tvTabProfileAvatar.text = initials
        binding.tvTabProfileName.text = user?.name ?: "Citizen User"
        binding.tvTabProfileHandle.text = user?.username ?: "@citizen_safe"
        binding.tvTabProfileBio.text = user?.bio ?: "Active safety contributor in Bandra West."
        binding.tvCountPosts.text = "${user?.postsCount ?: 2}"
        binding.tvCountFollowers.text = "${user?.followersCount ?: 4}"
        binding.tvCountFollowing.text = "${user?.followingCount ?: 3}"
        binding.tvTabEmergencyContact.text = user?.dynamicField1 ?: "+91 98200 12345 (Default Primary Contact)"

        updateProtectionStateUI()
    }

    private fun setupBottomNav() {
        binding.bottomNav.selectedItemId = R.id.nav_feed

        binding.bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_feed -> {
                    switchView(binding.swipeRefreshFeed)
                    binding.tvHeaderSubtitle.text = "Safety Social Hub • For You"
                    true
                }
                R.id.nav_radar -> {
                    switchView(binding.layoutRadarContainer)
                    binding.tvHeaderSubtitle.text = "Safe Radar & Live Heatmap"
                    loadRadarData()
                    true
                }
                R.id.nav_sos -> {
                    switchView(binding.layoutSosContainer)
                    binding.tvHeaderSubtitle.text = "Emergency Response & Motion Radar"
                    true
                }
                R.id.nav_channels -> {
                    switchView(binding.layoutChannelsContainer)
                    binding.tvHeaderSubtitle.text = "Official Broadcast Channels"
                    loadChannelsData()
                    true
                }
                R.id.nav_profile -> {
                    switchView(binding.layoutProfileContainer)
                    binding.tvHeaderSubtitle.text = "My Safety Profile & Network"
                    true
                }
                else -> false
            }
        }
    }

    private fun switchView(target: View) {
        binding.swipeRefreshFeed.visibility = View.GONE
        binding.layoutRadarContainer.visibility = View.GONE
        binding.layoutSosContainer.visibility = View.GONE
        binding.layoutChannelsContainer.visibility = View.GONE
        binding.layoutProfileContainer.visibility = View.GONE
        target.visibility = View.VISIBLE
    }

    private fun setupFeedAndStories() {
        val user = prefs.currentUser
        val initials = user?.avatar ?: user?.name?.take(2)?.uppercase() ?: "AS"

        // Stories Adapter setup
        storiesAdapter = StoriesAdapter(
            stories = emptyList(),
            currentUserInitials = initials,
            onStoryClicked = { story -> showStoryViewerDialog(story) },
            onAddStoryClicked = { showCreateStoryDialog() }
        )
        binding.rvStories.adapter = storiesAdapter

        // Feed Posts Adapter setup
        feedPostsAdapter = FeedPostsAdapter(
            posts = mutableListOf(),
            scope = lifecycleScope,
            onLikeClicked = { post, _ -> toggleLikeOnServer(post.id) }
        )
        binding.rvFeedPosts.adapter = feedPostsAdapter

        // Pull to refresh
        binding.swipeRefreshFeed.setOnRefreshListener {
            loadFeedData()
        }

        // Category Filter Buttons
        binding.btnFilterAll.setOnClickListener { switchCategory("ALL", binding.btnFilterAll) }
        binding.btnFilterAlerts.setOnClickListener { switchCategory("ALERTS", binding.btnFilterAlerts) }
        binding.btnFilterSafeRoutes.setOnClickListener { switchCategory("SAFE_ROUTE", binding.btnFilterSafeRoutes) }
        binding.btnFilterPolice.setOnClickListener { switchCategory("POLICE", binding.btnFilterPolice) }
        binding.btnFilterHelp.setOnClickListener { switchCategory("HELP_REQUEST", binding.btnFilterHelp) }

        // Post photo attachment
        binding.btnAttachPostPhoto.setOnClickListener {
            pickPostImageLauncher.launch("image/*")
        }

        // Quick Post Submission
        binding.btnSubmitPost.setOnClickListener {
            val text = binding.etPostInput.text.toString().trim()
            if (text.isEmpty()) {
                Toast.makeText(this, "Please write a safety update first", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val tags = listOf("COMMUNITY_UPDATE", "SAFE_ROUTE", "HAZARD_ALERT", "HELP_REQUEST", "POLICE_NOTICE")
            val selectedTag = tags.getOrElse(binding.spinnerPostTag.selectedItemPosition) { "COMMUNITY_UPDATE" }

            submitNewPost(text, selectedTag)
        }
    }

    private fun switchCategory(category: String, selectedBtn: View) {
        currentCategory = category
        val buttons = listOf(
            binding.btnFilterAll,
            binding.btnFilterAlerts,
            binding.btnFilterSafeRoutes,
            binding.btnFilterPolice,
            binding.btnFilterHelp
        )
        for (btn in buttons) {
            btn.setBackgroundColor(ContextCompat.getColor(this, R.color.card_dark))
            btn.setTextColor(ContextCompat.getColor(this, R.color.text_primary))
        }
        selectedBtn.setBackgroundColor(ContextCompat.getColor(this, R.color.primary))
        (selectedBtn as? android.widget.Button)?.setTextColor(ContextCompat.getColor(this, R.color.white))

        loadPosts()
    }

    private fun loadFeedData() {
        binding.swipeRefreshFeed.isRefreshing = true
        loadStories()
        loadPosts()
    }

    private fun loadStories() {
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.getStories()
                if (response.isSuccessful && response.body() != null) {
                    storiesAdapter.updateStories(response.body()!!)
                }
            } catch (e: Exception) {
                // Silently handle offline
            }
        }
    }

    private fun loadPosts() {
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.getFeedPosts(category = currentCategory)
                if (response.isSuccessful && response.body() != null) {
                    feedPostsAdapter.updatePosts(response.body()!!)
                }
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Feed network sync: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.swipeRefreshFeed.isRefreshing = false
            }
        }
    }

    private fun uploadPostImageFromUri(uri: Uri) {
        lifecycleScope.launch {
            try {
                Toast.makeText(this@MainActivity, "Uploading photo from device...", Toast.LENGTH_SHORT).show()
                val inputStream = contentResolver.openInputStream(uri) ?: return@launch
                val bytes = inputStream.readBytes()
                inputStream.close()

                val reqBody = bytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
                val part = MultipartBody.Part.createFormData("file", "upload_${System.currentTimeMillis()}.jpg", reqBody)

                val api = NetworkClient.getApiService(prefs)
                val res = api.uploadMedia("post", part)
                if (res.isSuccessful && res.body() != null) {
                    attachedPostMediaUrl = res.body()!!.url
                    binding.tvPostPhotoIndicator.visibility = View.VISIBLE
                    Toast.makeText(this@MainActivity, "Photo attached to post! ✓", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this@MainActivity, "Upload failed (${res.code()})", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Error uploading photo: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun uploadStoryImageFromUri(uri: Uri) {
        lifecycleScope.launch {
            try {
                Toast.makeText(this@MainActivity, "Uploading story photo from device...", Toast.LENGTH_SHORT).show()
                val inputStream = contentResolver.openInputStream(uri) ?: return@launch
                val bytes = inputStream.readBytes()
                inputStream.close()

                val reqBody = bytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
                val part = MultipartBody.Part.createFormData("file", "story_${System.currentTimeMillis()}.jpg", reqBody)

                val api = NetworkClient.getApiService(prefs)
                val res = api.uploadMedia("story", part)
                if (res.isSuccessful && res.body() != null) {
                    attachedStoryMediaUrl = res.body()!!.url
                    Toast.makeText(this@MainActivity, "Story photo attached! ✓", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this@MainActivity, "Story upload failed (${res.code()})", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Error uploading story photo: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun submitNewPost(content: String, tag: String) {
        val user = prefs.currentUser
        val req = CreatePostRequest(
            authorName = user?.name ?: "Aarohi Sharma",
            authorRole = user?.role ?: "user",
            authorId = user?.id,
            title = content.take(45),
            content = content,
            tag = tag,
            locationName = user?.location ?: "Bandra West, Mumbai",
            mediaUrl = attachedPostMediaUrl,
            mediaType = if (attachedPostMediaUrl != null) "image" else "text"
        )

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.createFeedPost(req)
                if (response.isSuccessful && response.body() != null) {
                    feedPostsAdapter.addPostAtTop(response.body()!!)
                    binding.etPostInput.text.clear()
                    attachedPostMediaUrl = null
                    binding.tvPostPhotoIndicator.visibility = View.GONE
                    binding.scrollFeed.smoothScrollTo(0, 0)
                    Toast.makeText(this@MainActivity, "✨ Safety post shared with community!", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this@MainActivity, "Failed to publish post (${response.code()})", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Posting error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun toggleLikeOnServer(postId: String) {
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                api.toggleLikePost(postId)
            } catch (ignored: Exception) {}
        }
    }

    private fun showStoryViewerDialog(story: StoryItem) {
        val dialog = Dialog(this, android.R.style.Theme_Black_NoTitleBar_Fullscreen)
        val dialogBinding = DialogStoryViewerBinding.inflate(layoutInflater)
        dialog.setContentView(dialogBinding.root)

        val initials = story.authorAvatar ?: story.authorName.take(2).uppercase()
        dialogBinding.tvStoryDialogAvatar.text = initials
        dialogBinding.tvStoryDialogAuthor.text = story.authorName
        dialogBinding.tvStoryDialogLocation.text = "📍 ${story.locationTag ?: "Community Safe Corridor"} • Active"
        dialogBinding.tvStoryTagPill.text = "🛡️ #${story.tag}"
        dialogBinding.tvStoryCaption.text = story.caption

        if (!story.pollQuestion.isNullOrBlank()) {
            dialogBinding.llStoryPoll.visibility = View.VISIBLE
            dialogBinding.tvStoryPollQuestion.text = story.pollQuestion
            dialogBinding.btnPollOptionA.text = "${story.pollOptionA ?: "Option A"} (${story.pollVotesA} votes)"
            dialogBinding.btnPollOptionB.text = "${story.pollOptionB ?: "Option B"} (${story.pollVotesB} votes)"

            dialogBinding.btnPollOptionA.setOnClickListener {
                story.pollVotesA += 1
                dialogBinding.btnPollOptionA.text = "${story.pollOptionA ?: "Option A"} (${story.pollVotesA} votes) ✓"
                Toast.makeText(this, "Vote registered: ${story.pollOptionA}", Toast.LENGTH_SHORT).show()
            }
            dialogBinding.btnPollOptionB.setOnClickListener {
                story.pollVotesB += 1
                dialogBinding.btnPollOptionB.text = "${story.pollOptionB ?: "Option B"} (${story.pollVotesB} votes) ✓"
                Toast.makeText(this, "Vote registered: ${story.pollOptionB}", Toast.LENGTH_SHORT).show()
            }
        } else {
            dialogBinding.llStoryPoll.visibility = View.GONE
        }

        dialogBinding.btnCloseStory.setOnClickListener {
            dialog.dismiss()
        }

        dialog.show()
    }

    private fun showCreateStoryDialog() {
        val user = prefs.currentUser
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 20, 40, 10)
        }

        val input = EditText(this).apply {
            hint = "e.g. Walking home via Linking Road corridor. Well lit!"
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.white))
            setHintTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
        }
        layout.addView(input)

        val btnPick = Button(this).apply {
            text = "📷 Attach Story Photo from Device"
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_primary))
            setBackgroundColor(ContextCompat.getColor(this@MainActivity, R.color.card_dark))
            setOnClickListener {
                pickStoryImageLauncher.launch("image/*")
            }
        }
        layout.addView(btnPick)

        AlertDialog.Builder(this, R.style.Theme_Perimeter)
            .setTitle("Post a 24h Safety Story")
            .setView(layout)
            .setPositiveButton("Publish Story") { _, _ ->
                val caption = input.text.toString().trim()
                if (caption.isNotEmpty()) {
                    val req = CreateStoryRequest(
                        authorName = user?.name ?: "Aarohi Sharma",
                        authorRole = user?.role ?: "user",
                        authorAvatar = user?.avatar ?: "AS",
                        authorId = user?.id,
                        caption = caption,
                        locationTag = user?.location ?: "Bandra West, Mumbai",
                        mediaUrl = attachedStoryMediaUrl,
                        pollQuestion = "Are you walking alone tonight?",
                        pollOptionA = "Yes, tracking on app",
                        pollOptionB = "No, with a buddy"
                    )
                    lifecycleScope.launch {
                        try {
                            val api = NetworkClient.getApiService(prefs)
                            val res = api.createStory(req)
                            if (res.isSuccessful) {
                                attachedStoryMediaUrl = null
                                loadStories()
                                Toast.makeText(this@MainActivity, "✨ Story published for 24 hours!", Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(this@MainActivity, "Failed to publish story: ${e.message}", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    // ==========================================
    // SAFE RADAR, HEATMAP & SAFE ROUTES
    // ==========================================

    private fun setupRadarSection() {
        binding.btnRadarRefreshGps.setOnClickListener {
            refreshRadarLocationAndScore()
        }

        binding.btnQuickDestBandra.setOnClickListener {
            binding.etRouteDestination.setText("19.0800, 72.8800")
            Toast.makeText(this, "Destination: Bandra Metro", Toast.LENGTH_SHORT).show()
        }

        binding.btnQuickDestBkc.setOnClickListener {
            binding.etRouteDestination.setText("19.0657, 72.8685")
            Toast.makeText(this, "Destination: BKC Transit Hub", Toast.LENGTH_SHORT).show()
        }

        binding.btnQuickDestAndheri.setOnClickListener {
            binding.etRouteDestination.setText("19.1136, 72.8697")
            Toast.makeText(this, "Destination: Andheri West Corridor", Toast.LENGTH_SHORT).show()
        }

        binding.btnCalculateSafeRoutes.setOnClickListener {
            calculateSafeRoutes()
        }
    }

    private fun loadRadarData() {
        refreshRadarLocationAndScore()
        loadRadarHeatmap()
    }

    private fun refreshRadarLocationAndScore() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
            fusedLocationClient.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, null).addOnSuccessListener { loc ->
                if (loc != null) {
                    currentRadarLat = loc.latitude
                    currentRadarLng = loc.longitude
                    binding.tvRadarCoordinates.text = "${"%.4f".format(currentRadarLat)}° N, ${"%.4f".format(currentRadarLng)}° E"
                    binding.tvRadarGpsStatus.text = "● High-Accuracy GPS Locked (±${loc.accuracy.toInt()}m)"
                }
                fetchSafetyScore(currentRadarLat, currentRadarLng)
            }.addOnFailureListener {
                fetchSafetyScore(currentRadarLat, currentRadarLng)
            }
        } else {
            fetchSafetyScore(currentRadarLat, currentRadarLng)
        }
    }

    private fun fetchSafetyScore(lat: Double, lng: Double) {
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.getSafetyScore(lat, lng)
                if (res.isSuccessful && res.body() != null) {
                    val score = res.body()!!
                    binding.tvRadarScoreValue.text = "${score.riskScore}"
                    binding.tvRadarRiskBadge.text = score.riskLabel ?: score.riskLevel
                    binding.tvRadarIncidentsCount.text = "${score.incidentCount} active platform incidents in this sector. Baseline NCRB index: ${score.ncrbBaselineScore ?: 50.0}."

                    if (score.riskScore <= 40) {
                        binding.cvRadarScoreCard.setCardBackgroundColor(Color.parseColor("#132F20"))
                        binding.cvRadarScoreCard.strokeColor = Color.parseColor("#059669")
                        binding.tvRadarScoreValue.setTextColor(Color.parseColor("#10B981"))
                    } else if (score.riskScore <= 65) {
                        binding.cvRadarScoreCard.setCardBackgroundColor(Color.parseColor("#2F2813"))
                        binding.cvRadarScoreCard.strokeColor = Color.parseColor("#D97706")
                        binding.tvRadarScoreValue.setTextColor(Color.parseColor("#F59E0B"))
                    } else {
                        binding.cvRadarScoreCard.setCardBackgroundColor(Color.parseColor("#2D1517"))
                        binding.cvRadarScoreCard.strokeColor = Color.parseColor("#7F1D1D")
                        binding.tvRadarScoreValue.setTextColor(Color.parseColor("#EF4444"))
                    }
                }
            } catch (e: Exception) {
                // Handled
            }
        }
    }

    private fun loadRadarHeatmap() {
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.getHeatmap("Mumbai")
                val incidents = res.body()?.incidents ?: emptyList()
                renderRadarIncidents(incidents)
            } catch (e: Exception) {
                // Handled
            }
        }
    }

    private fun renderRadarIncidents(incidents: List<HeatmapIncidentItem>) {
        binding.llRadarIncidentsList.removeAllViews()
        if (incidents.isEmpty()) {
            val tv = TextView(this).apply {
                text = "No active risk incidents reported in this sector. Area is secure! 🛡️"
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
                textSize = 12f
                setPadding(0, 10, 0, 10)
            }
            binding.llRadarIncidentsList.addView(tv)
            return
        }

        for (inc in incidents.take(5)) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(16, 12, 16, 12)
                background = ContextCompat.getDrawable(this@MainActivity, R.drawable.bg_pill_dark)
                val params = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, 0, 0, 10)
                }
                layoutParams = params
            }

            val titleRow = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
            }

            val tvId = TextView(this).apply {
                text = inc.incidentId
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.primary))
                textSize = 12f
                setTypeface(null, android.graphics.Typeface.BOLD)
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }

            val tvSev = TextView(this).apply {
                text = inc.severity
                setTextColor(if (inc.severity == "CRITICAL") Color.parseColor("#EF4444") else Color.parseColor("#F59E0B"))
                textSize = 11f
                setTypeface(null, android.graphics.Typeface.BOLD)
            }
            titleRow.addView(tvId)
            titleRow.addView(tvSev)
            card.addView(titleRow)

            val tvAddr = TextView(this).apply {
                text = "📍 ${inc.address ?: "Local Sector"}"
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
                textSize = 11f
                setPadding(0, 4, 0, 0)
            }
            card.addView(tvAddr)

            binding.llRadarIncidentsList.addView(card)
        }
    }

    private fun calculateSafeRoutes() {
        val destText = binding.etRouteDestination.text.toString().trim()
        val parts = destText.split(",").mapNotNull { it.trim().toDoubleOrNull() }
        if (parts.size < 2) {
            Toast.makeText(this, "Enter destination as: Lat, Lng (e.g. 19.0800, 72.8800)", Toast.LENGTH_SHORT).show()
            return
        }

        val toLat = parts[0]
        val toLng = parts[1]
        binding.llRadarRoutesResults.removeAllViews()
        Toast.makeText(this, "Calculating safe corridors...", Toast.LENGTH_SHORT).show()

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.getSafeRoutes(currentRadarLat, currentRadarLng, toLat, toLng)
                val routes = res.body()?.routes ?: emptyList()
                renderRadarRoutes(routes)
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Route analysis error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun renderRadarRoutes(routes: List<SafeRouteItem>) {
        binding.llRadarRoutesResults.removeAllViews()
        if (routes.isEmpty()) {
            val tv = TextView(this).apply {
                text = "No route corridors found."
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
                textSize = 12f
            }
            binding.llRadarRoutesResults.addView(tv)
            return
        }

        for (r in routes) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(16, 14, 16, 14)
                background = ContextCompat.getDrawable(this@MainActivity, R.drawable.bg_pill_dark)
                val params = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, 0, 0, 12)
                }
                layoutParams = params
            }

            val tvTitle = TextView(this).apply {
                text = "${if (r.isRecommendedSafety) "🛡️ RECOMMENDED: " else "⚡ "}${r.name}"
                setTextColor(if (r.isRecommendedSafety) Color.parseColor("#10B981") else ContextCompat.getColor(this@MainActivity, R.color.white))
                textSize = 13f
                setTypeface(null, android.graphics.Typeface.BOLD)
            }
            card.addView(tvTitle)

            val tvStats = TextView(this).apply {
                text = "📏 ${r.distanceKm} km • ~${r.durationMins} mins • Risk: ${r.safetyRiskScore}/100 (${r.riskLabel ?: r.riskLevel})"
                setTextColor(Color.parseColor(r.colorHex ?: "#FFFFFF"))
                textSize = 11f
                setPadding(0, 4, 0, 4)
            }
            card.addView(tvStats)

            val tvDesc = TextView(this).apply {
                text = r.description ?: "Evaluated Corridor"
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
                textSize = 11f
            }
            card.addView(tvDesc)

            binding.llRadarRoutesResults.addView(card)
        }
    }

    // ==========================================
    // OFFICIAL BROADCAST CHANNELS
    // ==========================================

    private fun loadChannelsData() {
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.getChannels()
                val channels = res.body() ?: emptyList()
                renderChannels(channels)
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Channels error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun renderChannels(channels: List<ChannelItem>) {
        binding.llChannelsContainer.removeAllViews()
        if (channels.isEmpty()) {
            val tv = TextView(this).apply {
                text = "No broadcast channels available."
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
                textSize = 13f
            }
            binding.llChannelsContainer.addView(tv)
            return
        }

        for (ch in channels) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(20, 16, 20, 16)
                background = ContextCompat.getDrawable(this@MainActivity, R.drawable.bg_pill_dark)
                val params = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, 0, 0, 16)
                }
                layoutParams = params
            }

            val headerRow = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
            }

            val tvAvatar = TextView(this).apply {
                text = ch.avatar ?: "📢"
                textSize = 22f
            }
            headerRow.addView(tvAvatar)

            val titleCol = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(16, 0, 0, 0)
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }

            val tvName = TextView(this).apply {
                text = ch.name
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.white))
                textSize = 15f
                setTypeface(null, android.graphics.Typeface.BOLD)
            }
            val tvMeta = TextView(this).apply {
                text = "Created by ${ch.creatorName} (${ch.creatorRole.uppercase()}) • 👥 ${ch.subscriberCount} subscribers"
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
                textSize = 11f
            }
            titleCol.addView(tvName)
            titleCol.addView(tvMeta)
            headerRow.addView(titleCol)

            card.addView(headerRow)

            val tvDesc = TextView(this).apply {
                text = ch.description
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
                textSize = 12f
                setPadding(0, 10, 0, 8)
            }
            card.addView(tvDesc)

            val posts = ch.recentPosts ?: emptyList()
            if (posts.isNotEmpty()) {
                val tvRecent = TextView(this).apply {
                    text = "LATEST BULLETINS:"
                    setTextColor(ContextCompat.getColor(this@MainActivity, R.color.primary_light))
                    textSize = 10f
                    setTypeface(null, android.graphics.Typeface.BOLD)
                    setPadding(0, 4, 0, 4)
                }
                card.addView(tvRecent)

                for (p in posts.take(2)) {
                    val tvPost = TextView(this).apply {
                        text = "• ${p.title}: ${p.content}"
                        setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_primary))
                        textSize = 11.5f
                        setPadding(0, 2, 0, 4)
                    }
                    card.addView(tvPost)
                }
            }

            binding.llChannelsContainer.addView(card)
        }
    }

    // ==========================================
    // FOLLOWERS & FOLLOWING DIALOGS
    // ==========================================

    private fun showFollowersDialog() {
        val user = prefs.currentUser
        val userId = user?.id ?: "usr_001"
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.getFollowers(userId)
                val followers = res.body() ?: emptyList()
                showUsersListDialog("My Followers (${followers.size})", followers, isFollowers = true)
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Failed to load followers: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showFollowingDialog() {
        val user = prefs.currentUser
        val userId = user?.id ?: "usr_001"
        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.getFollowing(userId)
                val following = res.body() ?: emptyList()
                showUsersListDialog("Following (${following.size})", following, isFollowers = false)
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Failed to load following: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showUsersListDialog(title: String, users: List<UserSocialProfile>, isFollowers: Boolean) {
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(30, 20, 30, 20)
        }

        if (users.isEmpty()) {
            val emptyTv = TextView(this).apply {
                text = if (isFollowers) "No followers yet." else "You are not following anyone yet."
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
                textSize = 13f
                setPadding(0, 20, 0, 20)
                gravity = android.view.Gravity.CENTER
            }
            layout.addView(emptyTv)
        } else {
            for (u in users) {
                val row = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = android.view.Gravity.CENTER_VERTICAL
                    setPadding(0, 10, 0, 10)
                }

                val avatarTv = TextView(this).apply {
                    text = u.avatar ?: "AS"
                    setTextColor(Color.WHITE)
                    textSize = 12f
                    setTypeface(null, android.graphics.Typeface.BOLD)
                    gravity = android.view.Gravity.CENTER
                    background = ContextCompat.getDrawable(this@MainActivity, R.drawable.bg_circle_dark)
                    val params = LinearLayout.LayoutParams(70, 70)
                    layoutParams = params
                }
                row.addView(avatarTv)

                val infoCol = LinearLayout(this).apply {
                    orientation = LinearLayout.VERTICAL
                    setPadding(16, 0, 0, 0)
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                }

                val nameTv = TextView(this).apply {
                    text = u.name
                    setTextColor(Color.WHITE)
                    textSize = 14f
                    setTypeface(null, android.graphics.Typeface.BOLD)
                }
                val handleTv = TextView(this).apply {
                    text = "${u.username} • ${u.badgeTitle ?: u.role}"
                    setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
                    textSize = 11f
                }
                infoCol.addView(nameTv)
                infoCol.addView(handleTv)
                row.addView(infoCol)

                val btnAction = Button(this).apply {
                    text = if (isFollowers) (if (u.isFollowing) "Following" else "+ Follow") else "Unfollow"
                    textSize = 10f
                    setBackgroundColor(ContextCompat.getColor(this@MainActivity, R.color.card_dark))
                    setTextColor(Color.WHITE)
                    setOnClickListener {
                        lifecycleScope.launch {
                            try {
                                val api = NetworkClient.getApiService(prefs)
                                if (isFollowers && !u.isFollowing) {
                                    api.followUser(u.id)
                                    u.isFollowing = true
                                    this@apply.text = "Following"
                                    Toast.makeText(this@MainActivity, "Followed ${u.name}!", Toast.LENGTH_SHORT).show()
                                } else {
                                    api.unfollowUser(u.id)
                                    u.isFollowing = false
                                    this@apply.text = "+ Follow"
                                    Toast.makeText(this@MainActivity, "Unfollowed ${u.name}", Toast.LENGTH_SHORT).show()
                                }
                            } catch (e: Exception) {
                                Toast.makeText(this@MainActivity, "Action failed: ${e.message}", Toast.LENGTH_SHORT).show()
                            }
                        }
                    }
                }
                row.addView(btnAction)

                layout.addView(row)
            }
        }

        AlertDialog.Builder(this, R.style.Theme_Perimeter)
            .setTitle(title)
            .setView(layout)
            .setPositiveButton("Close", null)
            .show()
    }

    private fun updateProtectionStateUI() {
        val isActive = prefs.isProtectionActive
        binding.switchProtection.isChecked = isActive

        if (isActive) {
            binding.tvProtectionStatus.text = getString(R.string.protection_active)
            binding.tvProtectionSubtitle.text = getString(R.string.protection_subtitle_active)
            binding.ivShieldStatus.setColorFilter(ContextCompat.getColor(this, R.color.status_safe))
            binding.cvFeedSosBanner.visibility = View.VISIBLE
        } else {
            binding.tvProtectionStatus.text = getString(R.string.protection_inactive)
            binding.tvProtectionSubtitle.text = getString(R.string.protection_subtitle_inactive)
            binding.ivShieldStatus.setColorFilter(ContextCompat.getColor(this, R.color.text_muted))
            binding.cvFeedSosBanner.visibility = View.GONE
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupListeners() {
        // Quick SOS Banner Button on Feed
        binding.btnQuickSosBanner.setOnClickListener {
            binding.bottomNav.selectedItemId = R.id.nav_sos
        }

        // Top Header Actions
        binding.ivNotifications.setOnClickListener {
            startActivity(Intent(this, NotificationCenterActivity::class.java))
        }

        binding.ivSettings.setOnClickListener {
            startActivity(Intent(this, ProfileSettingsActivity::class.java))
        }

        // Protection Switch Toggle
        binding.switchProtection.setOnCheckedChangeListener { _, isChecked ->
            if (isChecked) {
                SafetyProtectionService.startProtection(this)
                prefs.isProtectionActive = true
                Toast.makeText(this, "PERIMETER Double-Shake Protection Activated", Toast.LENGTH_SHORT).show()
            } else {
                SafetyProtectionService.stopProtection(this)
                prefs.isProtectionActive = false
                Toast.makeText(this, "Protection Session Stopped", Toast.LENGTH_SHORT).show()
            }
            updateProtectionStateUI()
        }

        binding.btnConfigSensitivity.setOnClickListener {
            startActivity(Intent(this, MotionProtectionActivity::class.java))
        }

        // SOS Hold Button
        binding.btnSos.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startHoldTimer()
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    cancelHoldTimer()
                    true
                }
                else -> false
            }
        }

        binding.btnViewHistory.setOnClickListener {
            startActivity(Intent(this, SosHistoryActivity::class.java))
        }

        // Profile Tab Actions: Followers & Following
        binding.llFollowersContainer.setOnClickListener {
            showFollowersDialog()
        }

        binding.llFollowingContainer.setOnClickListener {
            showFollowingDialog()
        }

        binding.btnProfileSettings.setOnClickListener {
            startActivity(Intent(this, ProfileSettingsActivity::class.java))
        }

        binding.btnProfileLogout.setOnClickListener {
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

    private fun startHoldTimer() {
        holdStartTime = System.currentTimeMillis()
        binding.sosHoldProgress.visibility = View.VISIBLE
        binding.sosHoldProgress.progress = 0

        holdJob = lifecycleScope.launch {
            while (true) {
                val elapsed = System.currentTimeMillis() - holdStartTime
                val progress = ((elapsed.toFloat() / holdDurationMs) * 100).toInt()
                binding.sosHoldProgress.progress = progress

                if (elapsed >= holdDurationMs) {
                    binding.sosHoldProgress.progress = 100
                    triggerManualSos()
                    break
                }
                delay(30)
            }
        }
    }

    private fun cancelHoldTimer() {
        holdJob?.cancel()
        holdJob = null
        binding.sosHoldProgress.visibility = View.GONE
        binding.sosHoldProgress.progress = 0
    }

    private fun triggerManualSos() {
        cancelHoldTimer()
        Toast.makeText(this, "🚨 Dispatched Emergency SOS to Police Command & Volunteers!", Toast.LENGTH_SHORT).show()

        lifecycleScope.launch {
            val user = prefs.currentUser
            var lat = 19.0760
            var lng = 72.8777
            var acc = 10.0f
            var addr = user?.location ?: "Live Geolocation Coordinates"

            try {
                if (ContextCompat.checkSelfPermission(this@MainActivity, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                    val loc = fusedLocationClient.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, null).await()
                    if (loc != null) {
                        lat = loc.latitude
                        lng = loc.longitude
                        acc = loc.accuracy
                        addr = "Lat: ${"%.4f".format(lat)}, Lng: ${"%.4f".format(lng)}"
                    }
                }
            } catch (e: Exception) {
                // Fallback coordinates
            }

            val req = SOSTriggerRequest(
                userName = user?.name ?: "Citizen",
                userId = user?.id,
                phone = user?.phone,
                triggerType = "MANUAL_HOLD",
                severity = "CRITICAL",
                location = LocationCoords(lat, lng, acc, addr),
                notes = "Emergency SOS triggered by citizen via app hold button."
            )

            var incidentId = "SOS-${System.currentTimeMillis()}"
            var caseId = "CAS-${System.currentTimeMillis()}"
            var status = "ACTIVE_DISPATCH"

            try {
                val api = NetworkClient.getApiService(prefs)
                val res = api.triggerSos(req)
                if (res.isSuccessful && res.body() != null) {
                    val body = res.body()!!
                    incidentId = body.incidentId
                    caseId = body.caseId
                    status = body.status
                    prefs.lastIncidentId = incidentId
                } else {
                    offlineQueue.enqueue(req)
                }
            } catch (e: Exception) {
                offlineQueue.enqueue(req)
            }

            LocationTrackingService.startTracking(this@MainActivity, incidentId)

            val emergencyIntent = Intent(this@MainActivity, EmergencySosActivity::class.java).apply {
                putExtra(EmergencySosActivity.EXTRA_INCIDENT_ID, incidentId)
                putExtra(EmergencySosActivity.EXTRA_CASE_ID, caseId)
                putExtra(EmergencySosActivity.EXTRA_STATUS, status)
                putExtra(EmergencySosActivity.EXTRA_LAT, lat)
                putExtra(EmergencySosActivity.EXTRA_LNG, lng)
                putExtra(EmergencySosActivity.EXTRA_ADDRESS, addr)
                putExtra(EmergencySosActivity.EXTRA_TRIGGER_TYPE, "MANUAL_HOLD")
            }
            startActivity(emergencyIntent)
        }
    }

    private fun refreshLocation() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            binding.tvCurrentLocation.text = "GPS permission not granted"
            return
        }

        fusedLocationClient.lastLocation.addOnSuccessListener { loc ->
            if (loc != null) {
                binding.tvCurrentLocation.text = "Lat: ${"%.4f".format(loc.latitude)}, Lng: ${"%.4f".format(loc.longitude)} (Accuracy ±${loc.accuracy.toInt()}m)"
            } else {
                binding.tvCurrentLocation.text = "Bandra West, Mumbai (Network estimate)"
            }
        }
    }

    private fun flushOfflineQueueIfAny() {
        if (offlineQueue.hasPending) {
            lifecycleScope.launch {
                val flushed = offlineQueue.flushQueue(NetworkClient.getApiService(prefs))
                if (flushed > 0) {
                    Toast.makeText(this@MainActivity, "Transmitted $flushed pending offline SOS incidents.", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}

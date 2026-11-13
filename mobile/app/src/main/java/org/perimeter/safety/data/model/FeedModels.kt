package org.perimeter.safety.data.model

import com.google.gson.annotations.SerializedName

data class FeedPostItem(
    @SerializedName("id") val id: String,
    @SerializedName("author_id") val authorId: String?,
    @SerializedName("author_name") val authorName: String,
    @SerializedName("author_role") val authorRole: String,
    @SerializedName("author_badge") val authorBadge: String?,
    @SerializedName("author_avatar") val authorAvatar: String?,
    @SerializedName("title") val title: String,
    @SerializedName("content") val content: String,
    @SerializedName("tag") val tag: String,
    @SerializedName("location_name") val locationName: String?,
    @SerializedName("media_url") val mediaUrl: String?,
    @SerializedName("media_type") val mediaType: String? = "image",
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("upvotes") var upvotes: Int = 0,
    @SerializedName("shares_count") val sharesCount: Int = 0,
    @SerializedName("saves_count") val savesCount: Int = 0,
    @SerializedName("verified_by_police") val verifiedByPolice: Boolean = false,
    @SerializedName("comments_count") val commentsCount: Int = 0,
    @SerializedName("is_liked") var isLiked: Boolean = false,
    @SerializedName("is_saved") var isSaved: Boolean = false
)

data class StoryItem(
    @SerializedName("id") val id: String,
    @SerializedName("author_name") val authorName: String,
    @SerializedName("author_role") val authorRole: String,
    @SerializedName("author_avatar") val authorAvatar: String?,
    @SerializedName("author_id") val authorId: String?,
    @SerializedName("caption") val caption: String,
    @SerializedName("tag") val tag: String,
    @SerializedName("bg_gradient") val bgGradient: String?,
    @SerializedName("media_url") val mediaUrl: String?,
    @SerializedName("media_type") val mediaType: String? = "gradient",
    @SerializedName("location_tag") val locationTag: String?,
    @SerializedName("poll_question") val pollQuestion: String?,
    @SerializedName("poll_option_a") val pollOptionA: String?,
    @SerializedName("poll_option_b") val pollOptionB: String?,
    @SerializedName("poll_votes_a") var pollVotesA: Int = 0,
    @SerializedName("poll_votes_b") var pollVotesB: Int = 0,
    @SerializedName("expires_at") val expiresAt: String?,
    @SerializedName("created_at") val createdAt: String
)

data class CreatePostRequest(
    @SerializedName("author_name") val authorName: String,
    @SerializedName("author_role") val authorRole: String = "user",
    @SerializedName("author_id") val authorId: String? = null,
    @SerializedName("title") val title: String,
    @SerializedName("content") val content: String,
    @SerializedName("tag") val tag: String = "COMMUNITY_UPDATE",
    @SerializedName("location_name") val locationName: String? = "Neighborhood Corridor",
    @SerializedName("media_url") val mediaUrl: String? = null,
    @SerializedName("media_type") val mediaType: String? = "image"
)

data class CreateStoryRequest(
    @SerializedName("author_name") val authorName: String,
    @SerializedName("author_role") val authorRole: String = "user",
    @SerializedName("author_avatar") val authorAvatar: String? = "U",
    @SerializedName("author_id") val authorId: String? = null,
    @SerializedName("caption") val caption: String,
    @SerializedName("tag") val tag: String = "SAFE_STATUS",
    @SerializedName("bg_gradient") val bgGradient: String? = "linear-gradient(135deg, #FF5A5F, #8B5CF6)",
    @SerializedName("media_url") val mediaUrl: String? = null,
    @SerializedName("location_tag") val locationTag: String? = null,
    @SerializedName("poll_question") val pollQuestion: String? = null,
    @SerializedName("poll_option_a") val pollOptionA: String? = null,
    @SerializedName("poll_option_b") val pollOptionB: String? = null
)

data class LikeToggleResponse(
    @SerializedName("status") val status: String,
    @SerializedName("post_id") val postId: String,
    @SerializedName("liked") val liked: Boolean,
    @SerializedName("likes_count") val likesCount: Int
)

data class StoryVoteRequest(
    @SerializedName("option") val option: String
)

data class ChannelItem(
    @SerializedName("id") val id: String,
    @SerializedName("creator_id") val creatorId: String?,
    @SerializedName("creator_name") val creatorName: String,
    @SerializedName("creator_role") val creatorRole: String,
    @SerializedName("name") val name: String,
    @SerializedName("description") val description: String,
    @SerializedName("category") val category: String?,
    @SerializedName("avatar") val avatar: String?,
    @SerializedName("subscriber_count") val subscriberCount: Int = 0,
    @SerializedName("is_subscribed") var isSubscribed: Boolean = false,
    @SerializedName("recent_posts") val recentPosts: List<ChannelPostItem>? = emptyList(),
    @SerializedName("created_at") val createdAt: String?
)

data class ChannelPostItem(
    @SerializedName("id") val id: String,
    @SerializedName("channel_id") val channelId: String?,
    @SerializedName("author_name") val authorName: String,
    @SerializedName("title") val title: String,
    @SerializedName("content") val content: String,
    @SerializedName("media_url") val mediaUrl: String?,
    @SerializedName("created_at") val createdAt: String?
)

data class UserSocialProfile(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("username") val username: String,
    @SerializedName("role") val role: String,
    @SerializedName("badge_title") val badgeTitle: String?,
    @SerializedName("avatar") val avatar: String?,
    @SerializedName("bio") val bio: String?,
    @SerializedName("location") val location: String?,
    @SerializedName("followers_count") val followersCount: Int = 0,
    @SerializedName("is_following") var isFollowing: Boolean = false
)

data class SafetyScoreResponse(
    @SerializedName("area") val area: String?,
    @SerializedName("risk_score") val riskScore: Double,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("risk_label") val riskLabel: String?,
    @SerializedName("color_hex") val colorHex: String?,
    @SerializedName("incident_count") val incidentCount: Int = 0,
    @SerializedName("crime_trend") val crimeTrend: String?,
    @SerializedName("ncrb_baseline_score") val ncrbBaselineScore: Double? = 50.0
)

data class SafeRoutesResponse(
    @SerializedName("status") val status: String,
    @SerializedName("routes") val routes: List<SafeRouteItem>?
)

data class SafeRouteItem(
    @SerializedName("route_id") val routeId: String,
    @SerializedName("name") val name: String,
    @SerializedName("distance_km") val distanceKm: Double,
    @SerializedName("duration_mins") val durationMins: Int,
    @SerializedName("safety_risk_score") val safetyRiskScore: Double,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("risk_label") val riskLabel: String?,
    @SerializedName("color_hex") val colorHex: String?,
    @SerializedName("is_fastest") val isFastest: Boolean = false,
    @SerializedName("is_recommended_safety") val isRecommendedSafety: Boolean = false,
    @SerializedName("description") val description: String?
)

data class HeatmapResponse(
    @SerializedName("status") val status: String,
    @SerializedName("city") val city: String?,
    @SerializedName("incidents") val incidents: List<HeatmapIncidentItem>?
)

data class HeatmapIncidentItem(
    @SerializedName("incident_id") val incidentId: String,
    @SerializedName("type") val type: String,
    @SerializedName("severity") val severity: String,
    @SerializedName("status") val status: String,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("address") val address: String?,
    @SerializedName("created_at") val createdAt: String?
)

data class MediaUploadResponse(
    @SerializedName("url") val url: String,
    @SerializedName("filename") val filename: String?,
    @SerializedName("content_type") val contentType: String?,
    @SerializedName("size") val size: Long?,
    @SerializedName("kind") val kind: String?
)


package org.perimeter.safety.data.api

import okhttp3.MultipartBody
import org.perimeter.safety.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // Authentication & Profile Endpoints
    @POST("auth/login")
    suspend fun login(@Body req: UserLoginRequest): Response<TokenResponse>

    @POST("auth/register")
    suspend fun register(@Body req: UserRegisterRequest): Response<TokenResponse>

    @GET("auth/me")
    suspend fun getCurrentUser(): Response<UserProfile>

    // SOS Emergency Dispatch Endpoints
    @POST("sos/trigger")
    suspend fun triggerSos(@Body req: SOSTriggerRequest): Response<SOSIncidentResponse>

    @GET("sos/active")
    suspend fun getActiveIncidents(): Response<List<SOSIncidentResponse>>

    @GET("sos/{incident_id}")
    suspend fun getIncident(@Path("incident_id") incidentId: String): Response<SOSIncidentResponse>

    @POST("sos/{incident_id}/stand-down")
    suspend fun standDownIncident(
        @Path("incident_id") incidentId: String,
        @Query("reason") reason: String = "user_stand_down"
    ): Response<StandDownResponse>

    // Real Geolocation Tracking
    @POST("location/update")
    suspend fun updateLocation(@Body req: LocationUpdateRequest): Response<LocationResponse>

    @GET("location/me")
    suspend fun getMyLocation(): Response<LocationResponse?>

    // Device Token & Push Notification Endpoints
    @POST("notifications/device-token")
    suspend fun registerDeviceToken(@Body req: DeviceTokenRegisterRequest): Response<DeviceTokenResponse>

    @DELETE("notifications/device-token")
    suspend fun unregisterDeviceToken(@Query("token") token: String): Response<Any>

    @GET("notifications/")
    suspend fun getNotifications(@Query("limit") limit: Int = 20): Response<List<NotificationItem>>

    @POST("notifications/{notification_id}/read")
    suspend fun markNotificationRead(@Path("notification_id") notificationId: String): Response<Any>

    // Feed & Community Social Endpoints
    @GET("feed/")
    suspend fun getFeedPosts(
        @Query("category") category: String = "ALL"
    ): Response<List<FeedPostItem>>

    @GET("feed/stories")
    suspend fun getStories(): Response<List<StoryItem>>

    @POST("feed/")
    suspend fun createFeedPost(@Body req: CreatePostRequest): Response<FeedPostItem>

    @POST("feed/stories")
    suspend fun createStory(@Body req: CreateStoryRequest): Response<StoryItem>

    @POST("social/posts/{post_id}/like")
    suspend fun toggleLikePost(@Path("post_id") postId: String): Response<LikeToggleResponse>

    // Social Follows Endpoints
    @GET("social/users/{user_id}/followers")
    suspend fun getFollowers(@Path("user_id") userId: String): Response<List<UserSocialProfile>>

    @GET("social/users/{user_id}/following")
    suspend fun getFollowing(@Path("user_id") userId: String): Response<List<UserSocialProfile>>

    @POST("social/users/{user_id}/follow")
    suspend fun followUser(@Path("user_id") userId: String): Response<Map<String, Any>>

    @POST("social/users/{user_id}/unfollow")
    suspend fun unfollowUser(@Path("user_id") userId: String): Response<Map<String, Any>>

    // Broadcast Channels Endpoints
    @GET("social/channels")
    suspend fun getChannels(): Response<List<ChannelItem>>

    @GET("social/channels/{channel_id}/posts")
    suspend fun getChannelPosts(@Path("channel_id") channelId: String): Response<List<ChannelPostItem>>

    // Safety Radar, Heatmap & Safe Routes
    @GET("safety-score")
    suspend fun getSafetyScore(
        @Query("lat") lat: Double,
        @Query("lng") lng: Double
    ): Response<SafetyScoreResponse>

    @GET("heatmap")
    suspend fun getHeatmap(
        @Query("city") city: String = "Mumbai"
    ): Response<HeatmapResponse>

    @GET("safe-routes")
    suspend fun getSafeRoutes(
        @Query("from_lat") fromLat: Double,
        @Query("from_lng") fromLng: Double,
        @Query("to_lat") toLat: Double,
        @Query("to_lng") toLng: Double
    ): Response<SafeRoutesResponse>

    // Media Upload Endpoint
    @Multipart
    @POST("media/upload")
    suspend fun uploadMedia(
        @Query("kind") kind: String = "post",
        @Part file: MultipartBody.Part
    ): Response<MediaUploadResponse>
}


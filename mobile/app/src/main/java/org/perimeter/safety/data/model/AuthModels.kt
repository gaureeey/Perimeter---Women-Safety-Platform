package org.perimeter.safety.data.model

import com.google.gson.annotations.SerializedName

data class UserLoginRequest(
    @SerializedName("identity") val identity: String,
    @SerializedName("password") val password: String
)

data class UserRegisterRequest(
    @SerializedName("name") val name: String,
    @SerializedName("email") val email: String,
    @SerializedName("phone") val phone: String,
    @SerializedName("password") val password: String,
    @SerializedName("role") val role: String = "user",
    @SerializedName("dynamic_field_1") val dynamicField1: String? = null,
    @SerializedName("dynamic_field_2") val dynamicField2: String? = null,
    @SerializedName("username") val username: String? = null,
    @SerializedName("bio") val bio: String? = null,
    @SerializedName("location") val location: String? = null
)

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("user") val user: UserProfile
)

data class UserProfile(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("username") val username: String?,
    @SerializedName("email") val email: String,
    @SerializedName("phone") val phone: String,
    @SerializedName("role") val role: String,
    @SerializedName("badge_title") val badgeTitle: String?,
    @SerializedName("avatar") val avatar: String?,
    @SerializedName("bio") val bio: String?,
    @SerializedName("location") val location: String?,
    @SerializedName("followers_count") val followersCount: Int = 0,
    @SerializedName("following_count") val followingCount: Int = 0,
    @SerializedName("posts_count") val postsCount: Int = 0,
    @SerializedName("dynamic_field_1") val dynamicField1: String?,
    @SerializedName("dynamic_field_2") val dynamicField2: String?
)


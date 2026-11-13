package org.perimeter.safety.data.api

import okhttp3.Interceptor
import okhttp3.Response
import org.perimeter.safety.data.local.AppPreferences

class AuthInterceptor(private val prefs: AppPreferences = AppPreferences()) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val token = prefs.authToken

        val requestBuilder = original.newBuilder()
            .header("Accept", "application/json")

        if (!token.isNullOrBlank()) {
            requestBuilder.header("Authorization", "Bearer $token")
        }

        return chain.proceed(requestBuilder.build())
    }
}


package org.perimeter.safety.data.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import org.perimeter.safety.data.local.AppPreferences
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkClient {

    private var currentBaseUrl: String? = null
    private var retrofitInstance: Retrofit? = null
    private var apiServiceInstance: ApiService? = null

    fun getApiService(prefs: AppPreferences = AppPreferences()): ApiService {
        val configuredUrl = prefs.apiBaseUrl

        if (apiServiceInstance == null || currentBaseUrl != configuredUrl) {
            currentBaseUrl = configuredUrl

            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val okHttpClient = OkHttpClient.Builder()
                .addInterceptor(AuthInterceptor(prefs))
                .addInterceptor(logging)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .build()

            retrofitInstance = Retrofit.Builder()
                .baseUrl(configuredUrl)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build()

            apiServiceInstance = retrofitInstance!!.create(ApiService::class.java)
        }

        return apiServiceInstance!!
    }

    fun resetClient() {
        apiServiceInstance = null
        retrofitInstance = null
        currentBaseUrl = null
    }
}


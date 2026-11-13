package org.perimeter.safety.data.local

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.perimeter.safety.PerimeterApplication
import org.perimeter.safety.data.api.ApiService
import org.perimeter.safety.data.model.SOSTriggerRequest

class OfflineSosQueue(context: Context = PerimeterApplication.instance) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    private val gson = Gson()

    @Synchronized
    fun enqueue(request: SOSTriggerRequest) {
        val list = getPendingList().toMutableList()
        list.add(request)
        saveList(list)
        Log.w(TAG, "Offline SOS request enqueued. Total pending: ${list.size}")
    }

    @Synchronized
    fun getPendingList(): List<SOSTriggerRequest> {
        val json = prefs.getString(KEY_QUEUE, null) ?: return emptyList()
        return try {
            val type = object : TypeToken<List<SOSTriggerRequest>>() {}.type
            gson.fromJson(json, type) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    @Synchronized
    fun remove(request: SOSTriggerRequest) {
        val list = getPendingList().toMutableList()
        list.removeAll { it.userName == request.userName && it.location.latitude == request.location.latitude }
        saveList(list)
    }

    @Synchronized
    fun clear() {
        prefs.edit().remove(KEY_QUEUE).apply()
    }

    val hasPending: Boolean
        get() = getPendingList().isNotEmpty()

    private fun saveList(list: List<SOSTriggerRequest>) {
        prefs.edit().putString(KEY_QUEUE, gson.toJson(list)).apply()
    }

    suspend fun flushQueue(apiService: ApiService): Int = withContext(Dispatchers.IO) {
        val pending = getPendingList()
        if (pending.isEmpty()) return@withContext 0

        var sentCount = 0
        for (req in pending) {
            try {
                val response = apiService.triggerSos(req)
                if (response.isSuccessful && response.body() != null) {
                    remove(req)
                    sentCount++
                    Log.i(TAG, "Successfully transmitted pending offline SOS: ${response.body()?.incidentId}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to flush pending SOS item: ${e.message}")
            }
        }
        sentCount
    }

    companion object {
        private const val TAG = "OfflineSosQueue"
        private const val PREF_NAME = "perimeter_offline_sos_queue"
        private const val KEY_QUEUE = "pending_sos_items"
    }
}


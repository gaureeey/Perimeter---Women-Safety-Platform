package org.perimeter.safety.util

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import android.view.View
import android.widget.ImageView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL

object ImageLoader {

    private val maxMemory = (Runtime.getRuntime().maxMemory() / 1024).toInt()
    private val cacheSize = maxMemory / 8

    private val memoryCache = object : LruCache<String, Bitmap>(cacheSize) {
        override fun sizeOf(key: String, bitmap: Bitmap): Int {
            return bitmap.byteCount / 1024
        }
    }

    fun loadImage(
        scope: CoroutineScope,
        imageView: ImageView,
        imageUrl: String?,
        onSuccess: (() -> Unit)? = null
    ) {
        if (imageUrl.isNullOrBlank()) {
            imageView.visibility = View.GONE
            return
        }

        imageView.visibility = View.VISIBLE
        val cached = memoryCache.get(imageUrl)
        if (cached != null) {
            imageView.setImageBitmap(cached)
            onSuccess?.invoke()
            return
        }

        // Set tag to prevent incorrect recycle binding in RecyclerView
        imageView.tag = imageUrl

        scope.launch(Dispatchers.IO) {
            val bitmap = downloadBitmap(imageUrl)
            if (bitmap != null) {
                memoryCache.put(imageUrl, bitmap)
                withContext(Dispatchers.Main) {
                    if (imageView.tag == imageUrl) {
                        imageView.setImageBitmap(bitmap)
                        imageView.visibility = View.VISIBLE
                        onSuccess?.invoke()
                    }
                }
            } else {
                withContext(Dispatchers.Main) {
                    if (imageView.tag == imageUrl) {
                        imageView.visibility = View.GONE
                    }
                }
            }
        }
    }

    private fun downloadBitmap(urlStr: String): Bitmap? {
        var connection: HttpURLConnection? = null
        var inputStream: InputStream? = null
        return try {
            val url = URL(urlStr)
            connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 8000
            connection.readTimeout = 8000
            connection.doInput = true
            connection.connect()

            if (connection.responseCode == HttpURLConnection.HTTP_OK) {
                inputStream = connection.inputStream
                BitmapFactory.decodeStream(inputStream)
            } else {
                null
            }
        } catch (e: Exception) {
            null
        } finally {
            try { inputStream?.close() } catch (ignored: Exception) {}
            try { connection?.disconnect() } catch (ignored: Exception) {}
        }
    }
}


package org.perimeter.safety.ui.notifications

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.launch
import org.perimeter.safety.R
import org.perimeter.safety.data.api.NetworkClient
import org.perimeter.safety.data.local.AppPreferences
import org.perimeter.safety.data.model.NotificationItem
import org.perimeter.safety.databinding.ActivityNotificationCenterBinding

class NotificationCenterActivity : AppCompatActivity() {

    private lateinit var binding: ActivityNotificationCenterBinding
    private val prefs by lazy { AppPreferences(this) }
    private val items = mutableListOf<NotificationItem>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityNotificationCenterBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.rvNotifications.layoutManager = LinearLayoutManager(this)
        binding.rvNotifications.adapter = NotificationAdapter(items)

        loadNotifications()
    }

    private fun loadNotifications() {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmptyState.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.getNotifications(30)
                if (response.isSuccessful && response.body() != null) {
                    items.clear()
                    items.addAll(response.body()!!)
                    binding.rvNotifications.adapter?.notifyDataSetChanged()

                    if (items.isEmpty()) {
                        binding.tvEmptyState.visibility = View.VISIBLE
                    }
                } else {
                    binding.tvEmptyState.visibility = View.VISIBLE
                }
            } catch (e: Exception) {
                binding.tvEmptyState.text = "Could not load notifications: ${e.message}"
                binding.tvEmptyState.visibility = View.VISIBLE
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private class NotificationAdapter(private val list: List<NotificationItem>) :
        RecyclerView.Adapter<NotificationAdapter.ViewHolder>() {

        class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
            val tvTitle: TextView = view.findViewById(R.id.tvNotifTitle)
            val tvSeverity: TextView = view.findViewById(R.id.tvNotifSeverity)
            val tvMessage: TextView = view.findViewById(R.id.tvNotifMessage)
            val tvTime: TextView = view.findViewById(R.id.tvNotifTime)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val v = LayoutInflater.from(parent.context).inflate(R.layout.item_notification, parent, false)
            return ViewHolder(v)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val item = list[position]
            holder.tvTitle.text = item.title
            holder.tvSeverity.text = item.severity
            holder.tvMessage.text = item.message
            holder.tvTime.text = item.createdAt

            val ctx = holder.itemView.context
            if (item.severity == "CRITICAL" || item.severity == "HIGH") {
                holder.tvSeverity.setTextColor(ContextCompat.getColor(ctx, R.color.sos_red))
            } else {
                holder.tvSeverity.setTextColor(ContextCompat.getColor(ctx, R.color.status_info))
            }
        }

        override fun getItemCount(): Int = list.size
    }
}


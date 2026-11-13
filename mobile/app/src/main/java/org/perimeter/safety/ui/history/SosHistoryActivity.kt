package org.perimeter.safety.ui.history

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
import org.perimeter.safety.data.model.SOSIncidentResponse
import org.perimeter.safety.databinding.ActivitySosHistoryBinding

class SosHistoryActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySosHistoryBinding
    private val prefs by lazy { AppPreferences(this) }
    private val items = mutableListOf<SOSIncidentResponse>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySosHistoryBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.rvHistory.layoutManager = LinearLayoutManager(this)
        binding.rvHistory.adapter = HistoryAdapter(items)

        loadHistory()
    }

    private fun loadHistory() {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmptyState.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = NetworkClient.getApiService(prefs)
                val response = api.getActiveIncidents()
                if (response.isSuccessful && response.body() != null) {
                    items.clear()
                    items.addAll(response.body()!!)
                    binding.rvHistory.adapter?.notifyDataSetChanged()

                    if (items.isEmpty()) {
                        binding.tvEmptyState.visibility = View.VISIBLE
                    }
                } else {
                    binding.tvEmptyState.visibility = View.VISIBLE
                }
            } catch (e: Exception) {
                binding.tvEmptyState.text = "Could not load history: ${e.message}"
                binding.tvEmptyState.visibility = View.VISIBLE
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private class HistoryAdapter(private val list: List<SOSIncidentResponse>) :
        RecyclerView.Adapter<HistoryAdapter.ViewHolder>() {

        class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
            val tvIncidentId: TextView = view.findViewById(R.id.tvItemIncidentId)
            val tvCaseId: TextView = view.findViewById(R.id.tvItemCaseId)
            val tvStatus: TextView = view.findViewById(R.id.tvItemStatus)
            val tvLocation: TextView = view.findViewById(R.id.tvItemLocation)
            val tvTime: TextView = view.findViewById(R.id.tvItemTime)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val v = LayoutInflater.from(parent.context).inflate(R.layout.item_sos_history, parent, false)
            return ViewHolder(v)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val item = list[position]
            holder.tvIncidentId.text = item.incidentId
            holder.tvCaseId.text = "Case ${item.caseId} • ${item.triggerType}"
            holder.tvStatus.text = item.status
            holder.tvLocation.text = item.location.address ?: "Lat: ${item.location.latitude}, Lng: ${item.location.longitude}"
            holder.tvTime.text = "Time: ${item.createdAt}"

            val ctx = holder.itemView.context
            if (item.status == "ACTIVE_DISPATCH") {
                holder.tvStatus.setTextColor(ContextCompat.getColor(ctx, R.color.sos_red))
            } else {
                holder.tvStatus.setTextColor(ContextCompat.getColor(ctx, R.color.status_safe))
            }
        }

        override fun getItemCount(): Int = list.size
    }
}


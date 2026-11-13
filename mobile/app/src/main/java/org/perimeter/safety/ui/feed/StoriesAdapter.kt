package org.perimeter.safety.ui.feed

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import org.perimeter.safety.data.model.StoryItem
import org.perimeter.safety.databinding.ItemStoryNodeBinding

class StoriesAdapter(
    private var stories: List<StoryItem>,
    private val currentUserInitials: String,
    private val onStoryClicked: (StoryItem) -> Unit,
    private val onAddStoryClicked: () -> Unit
) : RecyclerView.Adapter<StoriesAdapter.StoryViewHolder>() {

    fun updateStories(newStories: List<StoryItem>) {
        this.stories = newStories
        notifyDataSetChanged()
    }

    override fun getItemCount(): Int {
        // +1 for the "Add Your Story" entry
        return stories.size + 1
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): StoryViewHolder {
        val binding = ItemStoryNodeBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return StoryViewHolder(binding)
    }

    override fun onBindViewHolder(holder: StoryViewHolder, position: Int) {
        if (position == 0) {
            // First item: Add Your Story
            holder.binding.tvStoryAvatarInitials.text = currentUserInitials
            holder.binding.tvStoryAuthorName.text = "Your Story"
            holder.binding.tvAddStoryBadge.visibility = View.VISIBLE
            holder.itemView.setOnClickListener { onAddStoryClicked() }
        } else {
            val story = stories[position - 1]
            holder.binding.tvStoryAvatarInitials.text = story.authorAvatar ?: (story.authorName.take(2).uppercase())
            holder.binding.tvStoryAuthorName.text = story.authorName.split(" ").firstOrNull() ?: story.authorName
            holder.binding.tvAddStoryBadge.visibility = View.GONE
            holder.itemView.setOnClickListener { onStoryClicked(story) }
        }
    }

    class StoryViewHolder(val binding: ItemStoryNodeBinding) : RecyclerView.ViewHolder(binding.root)
}


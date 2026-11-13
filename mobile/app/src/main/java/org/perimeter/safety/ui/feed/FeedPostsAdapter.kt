package org.perimeter.safety.ui.feed

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.CoroutineScope
import org.perimeter.safety.R
import org.perimeter.safety.data.model.FeedPostItem
import org.perimeter.safety.databinding.ItemFeedPostBinding
import org.perimeter.safety.util.ImageLoader

class FeedPostsAdapter(
    private var posts: MutableList<FeedPostItem>,
    private val scope: CoroutineScope,
    private val onLikeClicked: (FeedPostItem, Int) -> Unit
) : RecyclerView.Adapter<FeedPostsAdapter.PostViewHolder>() {

    fun updatePosts(newPosts: List<FeedPostItem>) {
        this.posts = newPosts.toMutableList()
        notifyDataSetChanged()
    }

    fun addPostAtTop(post: FeedPostItem) {
        posts.add(0, post)
        notifyItemInserted(0)
    }

    override fun getItemCount(): Int = posts.size

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PostViewHolder {
        val binding = ItemFeedPostBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return PostViewHolder(binding)
    }

    override fun onBindViewHolder(holder: PostViewHolder, position: Int) {
        val post = posts[position]
        val context = holder.itemView.context

        // Author & Avatar
        holder.binding.tvPostAuthorName.text = post.authorName
        holder.binding.tvPostAvatar.text = post.authorAvatar ?: post.authorName.take(2).uppercase()

        // Role Badge
        when (post.authorRole.lowercase()) {
            "police" -> {
                holder.binding.tvPostAuthorBadge.text = "Police Command"
                holder.binding.tvPostAuthorBadge.setTextColor(ContextCompat.getColor(context, R.color.status_info))
            }
            "volunteer" -> {
                holder.binding.tvPostAuthorBadge.text = "Verified Responder"
                holder.binding.tvPostAuthorBadge.setTextColor(ContextCompat.getColor(context, R.color.status_safe))
            }
            "journalist" -> {
                holder.binding.tvPostAuthorBadge.text = "Press Desk"
                holder.binding.tvPostAuthorBadge.setTextColor(ContextCompat.getColor(context, R.color.primary_light))
            }
            else -> {
                holder.binding.tvPostAuthorBadge.text = "Citizen"
                holder.binding.tvPostAuthorBadge.setTextColor(ContextCompat.getColor(context, R.color.primary))
            }
        }

        // Location & Tag
        val loc = post.locationName ?: "Neighborhood Corridor"
        holder.binding.tvPostLocationAndTime.text = "📍 $loc"
        holder.binding.tvPostTag.text = "#${post.tag.replace('_', ' ')}"

        // Title & Content
        holder.binding.tvPostTitle.text = post.title
        holder.binding.tvPostContent.text = post.content

        // Police Verification Banner
        if (post.verifiedByPolice) {
            holder.binding.tvPoliceVerified.visibility = View.VISIBLE
        } else {
            holder.binding.tvPoliceVerified.visibility = View.GONE
        }

        // Post Image
        if (!post.mediaUrl.isNullOrBlank()) {
            ImageLoader.loadImage(scope, holder.binding.ivPostImage, post.mediaUrl)
        } else {
            holder.binding.ivPostImage.visibility = View.GONE
        }

        // Stats & Counters
        holder.binding.tvLikeCount.text = "${post.upvotes}"
        holder.binding.tvCommentCount.text = "${post.commentsCount}"
        holder.binding.tvShareCount.text = "${post.sharesCount}"

        // Like State
        if (post.isLiked) {
            holder.binding.ivHeartIcon.setImageResource(R.drawable.ic_heart_filled)
        } else {
            holder.binding.ivHeartIcon.setImageResource(R.drawable.ic_heart)
        }

        // Like Button Interaction
        holder.binding.btnLikePost.setOnClickListener {
            post.isLiked = !post.isLiked
            if (post.isLiked) {
                post.upvotes += 1
                holder.binding.ivHeartIcon.setImageResource(R.drawable.ic_heart_filled)
            } else {
                post.upvotes = (post.upvotes - 1).coerceAtLeast(0)
                holder.binding.ivHeartIcon.setImageResource(R.drawable.ic_heart)
            }
            holder.binding.tvLikeCount.text = "${post.upvotes}"
            onLikeClicked(post, position)
        }

        // Save Bookmark Toggle
        holder.binding.ivSavePost.setOnClickListener {
            post.isSaved = !post.isSaved
            holder.binding.ivSavePost.setColorFilter(
                if (post.isSaved) ContextCompat.getColor(context, R.color.primary)
                else ContextCompat.getColor(context, R.color.white)
            )
        }
    }

    class PostViewHolder(val binding: ItemFeedPostBinding) : RecyclerView.ViewHolder(binding.root)
}


from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# ----------------- Profile & User -----------------
class UserProfileDetail(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    email: str
    phone: str
    role: str
    badge_title: str
    avatar: str
    bio: Optional[str] = None
    location: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_private: bool = False
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_following: bool = False
    is_follow_pending: bool = False
    dynamic_field_1: Optional[str] = None
    dynamic_field_2: Optional[str] = None
    created_at: datetime

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    avatar: Optional[str] = None
    is_private: Optional[bool] = None
    dynamic_field_1: Optional[str] = None
    dynamic_field_2: Optional[str] = None

class UserSearchItem(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    badge_title: str
    avatar: str
    bio: Optional[str] = None
    location: Optional[str] = None
    followers_count: int = 0
    is_following: bool = False
    dynamic_field_1: Optional[str] = None
    dynamic_field_2: Optional[str] = None

# ----------------- Follows -----------------
class FollowUserResponse(BaseModel):
    status: str
    message: str
    is_following: bool
    is_pending: bool = False
    followers_count: int

class FollowRequestResponse(BaseModel):
    id: str
    requester_id: str
    requester_name: str
    requester_username: Optional[str] = None
    requester_avatar: str
    requester_role: str
    created_at: datetime

# ----------------- Comments & Likes -----------------
class CommentCreate(BaseModel):
    text: str

class CommentResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    user_name: str
    user_avatar: str
    user_role: str
    text: str
    created_at: datetime

class LikeToggleResponse(BaseModel):
    post_id: str
    is_liked: bool
    upvotes: int

class SaveToggleResponse(BaseModel):
    post_id: str
    is_saved: bool

class SharePostRequest(BaseModel):
    target: Optional[str] = "community_network"

class StoryPollVoteRequest(BaseModel):
    option: str  # "A" or "B"

# ----------------- Reels -----------------
class ReelCreate(BaseModel):
    caption: str
    video_url: str
    thumbnail_url: Optional[str] = None
    audio_title: Optional[str] = "Original Safety Audio — Perimeter Sound"
    duration_seconds: Optional[int] = 30

class ReelResponse(BaseModel):
    id: str
    author_id: Optional[str] = None
    author_name: str
    author_avatar: str
    author_role: str
    caption: str
    video_url: str
    thumbnail_url: Optional[str] = None
    audio_title: str
    duration_seconds: int
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    created_at: datetime

# ----------------- Direct Messages -----------------
class ConversationCreate(BaseModel):
    recipient_id: str

class MessageCreate(BaseModel):
    text: str
    media_url: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_avatar: str
    text: str
    media_url: Optional[str] = None
    is_read: bool
    created_at: datetime

class ConversationResponse(BaseModel):
    id: str
    title: str
    is_group: bool
    recipient_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_avatar: Optional[str] = None
    recipient_role: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime

# ----------------- Broadcast Channels -----------------
class ChannelCreate(BaseModel):
    name: str
    description: str
    category: str = "SAFETY_ALERTS"
    avatar: Optional[str] = "📢"

class ChannelPostCreate(BaseModel):
    title: str
    content: str
    media_url: Optional[str] = None

class ChannelPostResponse(BaseModel):
    id: str
    channel_id: str
    author_name: str
    title: str
    content: str
    media_url: Optional[str] = None
    created_at: datetime

class ChannelResponse(BaseModel):
    id: str
    creator_id: str
    creator_name: str
    creator_role: str
    name: str
    description: str
    category: str
    avatar: str
    subscriber_count: int = 0
    is_subscribed: bool = False
    recent_posts: List[ChannelPostResponse] = []
    created_at: datetime

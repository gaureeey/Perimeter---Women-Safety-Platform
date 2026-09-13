from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import uuid

class Follow(Base):
    __tablename__ = "social_follows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id = Column(String, ForeignKey("users.id"), nullable=False)
    following_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_user_follow'),
    )

class FollowRequest(Base):
    __tablename__ = "social_follow_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    target_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

class PostLike(Base):
    __tablename__ = "social_post_likes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("feed_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uq_post_user_like'),
    )

class PostComment(Base):
    __tablename__ = "social_post_comments"

    id = Column(String, primary_key=True, default=lambda: f"cmt_{uuid.uuid4().hex[:6]}")
    post_id = Column(String, ForeignKey("feed_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user_name = Column(String, nullable=False)
    user_avatar = Column(String, nullable=False, default="U")
    user_role = Column(String, nullable=False, default="user")
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PostShare(Base):
    __tablename__ = "social_post_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("feed_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    share_target = Column(String, default="community_network")
    created_at = Column(DateTime, default=datetime.utcnow)

class PostSave(Base):
    __tablename__ = "social_post_saves"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("feed_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uq_post_user_save'),
    )

class StoryView(Base):
    __tablename__ = "social_story_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String, ForeignKey("stories.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)

class StoryPollVote(Base):
    __tablename__ = "social_story_poll_votes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String, ForeignKey("stories.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    selected_option = Column(String, nullable=False)  # e.g. "A" or "B"
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('story_id', 'user_id', name='uq_story_user_poll_vote'),
    )

class Reel(Base):
    __tablename__ = "social_reels"

    id = Column(String, primary_key=True, default=lambda: f"reel_{uuid.uuid4().hex[:6]}")
    author_id = Column(String, nullable=True)
    author_name = Column(String, nullable=False)
    author_avatar = Column(String, nullable=False, default="U")
    author_role = Column(String, nullable=False, default="user")
    caption = Column(String, nullable=False)
    video_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    audio_title = Column(String, default="Original Safety Audio — Perimeter Sound")
    duration_seconds = Column(Integer, default=30)  # Max 90s
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReelLike(Base):
    __tablename__ = "social_reel_likes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reel_id = Column(String, ForeignKey("social_reels.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('reel_id', 'user_id', name='uq_reel_user_like'),
    )

class Conversation(Base):
    __tablename__ = "social_conversations"

    id = Column(String, primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex[:6]}")
    title = Column(String, nullable=True)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMember(Base):
    __tablename__ = "social_conversation_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("social_conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="members")

class Message(Base):
    __tablename__ = "social_messages"

    id = Column(String, primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:6]}")
    conversation_id = Column(String, ForeignKey("social_conversations.id"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    sender_name = Column(String, nullable=False)
    sender_avatar = Column(String, nullable=False, default="U")
    text = Column(Text, nullable=False)
    media_url = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class BroadcastChannel(Base):
    __tablename__ = "social_broadcast_channels"

    id = Column(String, primary_key=True, default=lambda: f"chan_{uuid.uuid4().hex[:6]}")
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    creator_name = Column(String, nullable=False)
    creator_role = Column(String, nullable=False)  # police, journalist, admin
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, default="SAFETY_ALERTS")  # POLICE_BULLETIN, INVESTIGATIVE_PRESS, DISPATCH_ALERTS
    avatar = Column(String, default="📢")
    subscriber_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("ChannelPost", back_populates="channel", cascade="all, delete-orphan")
    subscribers = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")

class ChannelMember(Base):
    __tablename__ = "social_channel_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id = Column(String, ForeignKey("social_broadcast_channels.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    channel = relationship("BroadcastChannel", back_populates="subscribers")

    __table_args__ = (
        UniqueConstraint('channel_id', 'user_id', name='uq_channel_member'),
    )

class ChannelPost(Base):
    __tablename__ = "social_channel_posts"

    id = Column(String, primary_key=True, default=lambda: f"cp_{uuid.uuid4().hex[:6]}")
    channel_id = Column(String, ForeignKey("social_broadcast_channels.id"), nullable=False)
    author_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    media_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    channel = relationship("BroadcastChannel", back_populates="posts")

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from datetime import datetime, timedelta
from app.db.session import Base
import uuid

class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(String, primary_key=True, default=lambda: f"post_{uuid.uuid4().hex[:6]}")
    author_id = Column(String, nullable=True)
    author_name = Column(String, nullable=False)
    author_role = Column(String, nullable=False)  # user, volunteer, journalist, police, admin
    author_badge = Column(String, nullable=False, default="Citizen User")
    author_avatar = Column(String, nullable=False, default="U")
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tag = Column(String, default="COMMUNITY_UPDATE")  # SAFE_ROUTE, HAZARD_ALERT, POLICE_NOTICE, PRESS_REPORT, HELP_REQUEST
    location_name = Column(String, default="Neighborhood Corridor")
    media_url = Column(String, nullable=True)
    media_type = Column(String, default="image")  # image, video, carousel, text
    media_urls = Column(Text, nullable=True)  # JSON array for up to 10 media items
    upvotes = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)
    verified_by_police = Column(Boolean, default=False)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Story(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True, default=lambda: f"story_{uuid.uuid4().hex[:6]}")
    author_id = Column(String, nullable=True)
    author_name = Column(String, nullable=False)
    author_role = Column(String, nullable=False)  # user, volunteer, journalist, police, admin
    author_avatar = Column(String, nullable=False, default="U")
    caption = Column(String, nullable=False)
    tag = Column(String, default="SAFE_STATUS")  # SAFE_STATUS, PATROL_ACTIVE, PRESS_UPDATE, POLICE_ALERT, SAFE_CORRIDOR
    bg_gradient = Column(String, default="linear-gradient(135deg, #111528, #1E293B)")
    media_url = Column(String, nullable=True)
    media_type = Column(String, default="gradient")  # gradient, image, video
    
    # Interactive Story features (Polls, Quizzes, Location Tag)
    location_tag = Column(String, nullable=True)
    poll_question = Column(String, nullable=True)
    poll_option_a = Column(String, nullable=True)
    poll_option_b = Column(String, nullable=True)
    poll_votes_a = Column(Integer, default=0)
    poll_votes_b = Column(Integer, default=0)
    
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    created_at = Column(DateTime, default=datetime.utcnow)

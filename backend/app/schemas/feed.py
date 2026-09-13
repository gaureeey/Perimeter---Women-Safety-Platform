from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class StoryCreate(BaseModel):
    author_name: str
    author_role: str = "user"  # user, volunteer, journalist, police, admin
    author_avatar: Optional[str] = "U"
    author_id: Optional[str] = None
    caption: str
    tag: str = "SAFE_STATUS"
    bg_gradient: Optional[str] = "linear-gradient(135deg, #111528, #1E293B)"
    media_url: Optional[str] = None
    media_type: Optional[str] = "gradient"
    location_tag: Optional[str] = None
    poll_question: Optional[str] = None
    poll_option_a: Optional[str] = None
    poll_option_b: Optional[str] = None

class StoryResponse(BaseModel):
    id: str
    author_name: str
    author_role: str
    author_avatar: str
    author_id: Optional[str] = None
    caption: str
    tag: str
    bg_gradient: str
    media_url: Optional[str] = None
    media_type: str = "gradient"
    location_tag: Optional[str] = None
    poll_question: Optional[str] = None
    poll_option_a: Optional[str] = None
    poll_option_b: Optional[str] = None
    poll_votes_a: int = 0
    poll_votes_b: int = 0
    expires_at: Optional[datetime] = None
    created_at: datetime

class FeedPostCreate(BaseModel):
    author_name: str
    author_role: str = "user"  # user, volunteer, journalist, police
    author_id: Optional[str] = None
    title: str
    content: str
    tag: str = "COMMUNITY_UPDATE"  # SAFE_ROUTE, HAZARD_ALERT, POLICE_NOTICE, PRESS_REPORT, HELP_REQUEST
    location_name: Optional[str] = "Neighborhood Corridor"
    media_url: Optional[str] = None
    media_type: Optional[str] = "image"
    media_urls: Optional[str] = None

class FeedPostResponse(BaseModel):
    id: str
    author_id: Optional[str] = None
    author_name: str
    author_role: str
    author_badge: str
    author_avatar: str
    title: str
    content: str
    tag: str
    location_name: str
    media_url: Optional[str] = None
    media_type: str = "image"
    media_urls: Optional[str] = None
    created_at: datetime
    upvotes: int = 0
    shares_count: int = 0
    saves_count: int = 0
    verified_by_police: bool = False
    comments_count: int = 0
    is_liked: Optional[bool] = False
    is_saved: Optional[bool] = False

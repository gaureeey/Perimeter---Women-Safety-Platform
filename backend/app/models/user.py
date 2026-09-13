from sqlalchemy import Column, String, Boolean, Integer, DateTime
from datetime import datetime
from app.db.session import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # user, volunteer, journalist, police, admin
    badge_title = Column(String, nullable=False, default="Citizen User")
    avatar = Column(String, nullable=False, default="U")
    bio = Column(String, nullable=True, default="Active community safety member.")
    location = Column(String, nullable=True, default="Mumbai Metro Area")
    profile_image_url = Column(String, nullable=True)
    is_private = Column(Boolean, default=False)
    
    # Social counters
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)

    dynamic_field_1 = Column(String, nullable=True)  # Emergency Contact, Volunteer ID, Press ID, Police Badge
    dynamic_field_2 = Column(String, nullable=True)  # Safe Zone, Patrol Sector, Media Outlet, Precinct
    created_at = Column(DateTime, default=datetime.utcnow)

from typing import Optional
from pydantic import BaseModel, EmailStr

class UserRegisterRequest(BaseModel):
    name: str
    username: Optional[str] = None
    email: EmailStr
    phone: str
    password: str
    role: str = "user"  # user, volunteer, journalist, police, admin
    bio: Optional[str] = "Active community safety member."
    location: Optional[str] = "Mumbai Metro Area"
    dynamic_field_1: Optional[str] = None  # Emergency contact, Vol ID, Press ID, Police Badge
    dynamic_field_2: Optional[str] = None  # Safe zone, Patrol area, News outlet, Police Station

class UserLoginRequest(BaseModel):
    identity: str  # email, phone, username, or badge
    password: str

class UserProfileResponse(BaseModel):
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
    dynamic_field_1: Optional[str] = None
    dynamic_field_2: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse

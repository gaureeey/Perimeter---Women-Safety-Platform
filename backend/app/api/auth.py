"""
PERIMETER Authentication & Profiles API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserProfileResponse
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication & Profiles"])

ROLE_BADGE_MAP = {
    "user": "Citizen User",
    "volunteer": "Verified Responder",
    "journalist": "Press Reporter",
    "police": "City Police Command",
    "admin": "Super Administrator"
}

from app.models.social import Follow

def build_profile(user: User, db: Session = None) -> UserProfileResponse:
    followers = user.followers_count or 0
    following = user.following_count or 0
    posts = user.posts_count or 0
    if db:
        followers = db.query(Follow).filter(Follow.following_id == user.id).count()
        following = db.query(Follow).filter(Follow.follower_id == user.id).count()

    uname = user.username or f"@{user.name.lower().replace(' ', '_')}"
    return UserProfileResponse(
        id=user.id,
        name=user.name,
        username=uname,
        email=user.email,
        phone=user.phone,
        role=user.role,
        badge_title=user.badge_title,
        avatar=user.avatar,
        bio=user.bio or "Active community safety member.",
        location=user.location or "Mumbai Metro Area",
        profile_image_url=user.profile_image_url,
        is_private=bool(user.is_private),
        followers_count=followers,
        following_count=following,
        posts_count=posts,
        dynamic_field_1=user.dynamic_field_1,
        dynamic_field_2=user.dynamic_field_2
    )

@router.post("/register", response_model=TokenResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    One-time user registration:
    Saves user credentials with hashed password into the database,
    and returns a signed persistent JWT token along with the user's role profile.
    """
    clean_email = req.email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please register with a different email."
        )

    initials = "".join([part[0] for part in req.name.split() if part])[:2].upper() or "P"
    user_id = f"{req.role}_{uuid.uuid4().hex[:6]}"
    badge_title = ROLE_BADGE_MAP.get(req.role, "Citizen User")

    # Generate unique username
    base_username = req.username.strip().lstrip('@') if req.username else req.name.lower().replace(" ", "_")
    uname = f"@{base_username}"
    # Ensure uniqueness
    if db.query(User).filter(User.username == uname).first():
        uname = f"@{base_username}_{uuid.uuid4().hex[:4]}"

    new_user = User(
        id=user_id,
        name=req.name.strip(),
        username=uname,
        email=clean_email,
        phone=req.phone.strip(),
        password=get_password_hash(req.password),
        role=req.role,
        badge_title=badge_title,
        avatar=initials,
        bio=req.bio or "Active community safety member.",
        location=req.location or "Mumbai Metro Area",
        followers_count=0,
        following_count=0,
        posts_count=0,
        dynamic_field_1=req.dynamic_field_1,
        dynamic_field_2=req.dynamic_field_2
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    profile = build_profile(new_user, db)
    token = create_access_token(data={"sub": new_user.id, "email": new_user.email, "role": new_user.role})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=profile
    )

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate an existing user or pre-seeded role persona, returning a JWT token.
    """
    identity = req.identity.strip().lower()
    user = db.query(User).filter(
        (User.email == identity) | (User.dynamic_field_1 == req.identity.strip())
    ).first()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/badge identity or password."
        )

    profile = build_profile(user, db)
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=profile
    )

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate session and retrieve the authenticated user's profile.
    """
    return build_profile(current_user, db)

@router.get("/users", response_model=List[UserProfileResponse])
def get_all_users(db: Session = Depends(get_db)):
    """
    Retrieve registered users across all roles for coordination and directory.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [build_profile(u, db) for u in users]

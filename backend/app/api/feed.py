"""
PERIMETER Social Safety Feed & Stories API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.db.session import get_db
from app.models.feed import FeedPost, Story
from app.models.user import User
from app.models.social import Follow, PostLike, PostSave, StoryView
from app.schemas.feed import FeedPostCreate, FeedPostResponse, StoryCreate, StoryResponse
from app.core.security import get_current_user, get_optional_user, security_bearer, decode_access_token
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter(prefix="/feed", tags=["Social Safety Feed & Stories"])

ROLE_BADGE_MAP = {
    "user": "Citizen User",
    "volunteer": "Verified Responder",
    "journalist": "Press Reporter",
    "police": "City Police Command",
    "admin": "Super Administrator"
}

@router.get("/stories", response_model=List[StoryResponse])
def get_stories(db: Session = Depends(get_db)):
    """
    Retrieve active safety stories and patrol statuses that have not expired.
    """
    now = datetime.utcnow()
    # Filter stories created within 24 hours or with future expires_at
    stories = db.query(Story).filter(
        or_(
            Story.expires_at == None,
            Story.expires_at > now
        )
    ).order_by(Story.created_at.desc()).all()

    return [
        StoryResponse(
            id=s.id,
            author_id=s.author_id,
            author_name=s.author_name,
            author_role=s.author_role,
            author_avatar=s.author_avatar,
            caption=s.caption,
            tag=s.tag,
            bg_gradient=s.bg_gradient,
            media_url=s.media_url,
            media_type=s.media_type or "gradient",
            location_tag=s.location_tag,
            poll_question=s.poll_question,
            poll_option_a=s.poll_option_a,
            poll_option_b=s.poll_option_b,
            poll_votes_a=s.poll_votes_a or 0,
            poll_votes_b=s.poll_votes_b or 0,
            expires_at=s.expires_at,
            created_at=s.created_at
        )
        for s in stories
    ]

@router.post("/stories", response_model=StoryResponse)
def create_story(
    req: StoryCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Publish a 24h safety story or responder beacon with optional interactive polls.
    """
    valid_user = current_user if isinstance(current_user, User) else None
    author_name = valid_user.name if valid_user else req.author_name
    author_role = valid_user.role if valid_user else req.author_role
    author_id = valid_user.id if valid_user else req.author_id
    initials = valid_user.avatar if valid_user else (req.author_avatar or "".join([w[0] for w in author_name.split() if w])[:2].upper() or "U")

    story = Story(
        id=f"story_{uuid.uuid4().hex[:6]}",
        author_id=author_id,
        author_name=author_name,
        author_role=author_role,
        author_avatar=initials,
        caption=req.caption.strip(),
        tag=req.tag,
        bg_gradient=req.bg_gradient or "linear-gradient(135deg, #111528, #1E293B)",
        media_url=req.media_url,
        media_type=req.media_type or "gradient",
        location_tag=req.location_tag,
        poll_question=req.poll_question,
        poll_option_a=req.poll_option_a,
        poll_option_b=req.poll_option_b,
        poll_votes_a=0,
        poll_votes_b=0,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    return StoryResponse(
        id=story.id,
        author_id=story.author_id,
        author_name=story.author_name,
        author_role=story.author_role,
        author_avatar=story.author_avatar,
        caption=story.caption,
        tag=story.tag,
        bg_gradient=story.bg_gradient,
        media_url=story.media_url,
        media_type=story.media_type or "gradient",
        location_tag=story.location_tag,
        poll_question=story.poll_question,
        poll_option_a=story.poll_option_a,
        poll_option_b=story.poll_option_b,
        poll_votes_a=0,
        poll_votes_b=0,
        expires_at=story.expires_at,
        created_at=story.created_at
    )

@router.get("/", response_model=List[FeedPostResponse])
def get_feed_posts(
    category: Optional[str] = Query("ALL", description="Filter category: ALL, FOLLOWING, ALERTS, POLICE, HELP_REQUEST"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve community safety updates, alerts, and verified police notices with personalized following & interaction flags.
    """
    valid_user = current_user if isinstance(current_user, User) else None
    query = db.query(FeedPost)

    if category == "POLICE":
        query = query.filter(or_(FeedPost.author_role == "police", FeedPost.tag == "POLICE_NOTICE"))
    elif category == "ALERTS":
        query = query.filter(FeedPost.tag.in_(["HAZARD_ALERT", "POLICE_NOTICE", "SAFE_ROUTE"]))
    elif category == "HELP_REQUEST":
        query = query.filter(FeedPost.tag == "HELP_REQUEST")
    elif category == "FOLLOWING" and valid_user:
        following_ids = [f.following_id for f in db.query(Follow).filter(Follow.follower_id == valid_user.id).all()]
        following_users = db.query(User.name).filter(User.id.in_(following_ids)).all() if following_ids else []
        following_names = [u[0] for u in following_users]
        query = query.filter(
            or_(
                FeedPost.author_id.in_(following_ids),
                FeedPost.author_name.in_(following_names)
            )
        )

    posts = query.order_by(FeedPost.created_at.desc()).limit(50).all()

    # Pre-fetch user likes and saves for efficient flag mapping
    user_liked_post_ids = set()
    user_saved_post_ids = set()
    if valid_user:
        user_liked_post_ids = {l.post_id for l in db.query(PostLike).filter(PostLike.user_id == valid_user.id).all()}
        user_saved_post_ids = {s.post_id for s in db.query(PostSave).filter(PostSave.user_id == valid_user.id).all()}

    results = []
    for p in posts:
        results.append(FeedPostResponse(
            id=p.id,
            author_id=p.author_id,
            author_name=p.author_name,
            author_role=p.author_role,
            author_badge=p.author_badge,
            author_avatar=p.author_avatar,
            title=p.title,
            content=p.content,
            tag=p.tag,
            location_name=p.location_name or "Local Geofence",
            media_url=p.media_url,
            media_type=p.media_type or "image",
            media_urls=p.media_urls,
            created_at=p.created_at,
            upvotes=p.upvotes or 0,
            shares_count=p.shares_count or 0,
            saves_count=p.saves_count or 0,
            verified_by_police=bool(p.verified_by_police),
            comments_count=p.comments_count or 0,
            is_liked=(p.id in user_liked_post_ids),
            is_saved=(p.id in user_saved_post_ids)
        ))
    return results

@router.post("/", response_model=FeedPostResponse)
def create_feed_post(
    req: FeedPostCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Publish a new community safety post, incident alert, or verified notice.
    """
    valid_user = current_user if isinstance(current_user, User) else None
    author_name = valid_user.name if valid_user else req.author_name
    author_role = valid_user.role if valid_user else req.author_role
    author_id = valid_user.id if valid_user else req.author_id
    initials = valid_user.avatar if valid_user else "".join([w[0] for w in author_name.split() if w])[:2].upper() or "U"
    badge = ROLE_BADGE_MAP.get(author_role, "Citizen User")

    post = FeedPost(
        id=f"post_{uuid.uuid4().hex[:6]}",
        author_id=author_id,
        author_name=author_name,
        author_role=author_role,
        author_badge=badge,
        author_avatar=initials,
        title=req.title.strip(),
        content=req.content.strip(),
        tag=req.tag,
        location_name=req.location_name or "Neighborhood Corridor",
        media_url=req.media_url,
        media_type=req.media_type or "image",
        media_urls=req.media_urls,
        upvotes=0,
        shares_count=0,
        saves_count=0,
        verified_by_police=(author_role == "police"),
        comments_count=0
    )
    db.add(post)

    # Increment user post counter if registered
    if valid_user:
        valid_user.posts_count = (valid_user.posts_count or 0) + 1

    db.commit()
    db.refresh(post)

    return FeedPostResponse(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author_name,
        author_role=post.author_role,
        author_badge=post.author_badge,
        author_avatar=post.author_avatar,
        title=post.title,
        content=post.content,
        tag=post.tag,
        location_name=post.location_name,
        media_url=post.media_url,
        media_type=post.media_type,
        media_urls=post.media_urls,
        created_at=post.created_at,
        upvotes=0,
        shares_count=0,
        saves_count=0,
        verified_by_police=post.verified_by_police,
        comments_count=0,
        is_liked=False,
        is_saved=False
    )

@router.post("/{post_id}/upvote")
def upvote_post(post_id: str, db: Session = Depends(get_db)):
    """
    Upvote / verify community post usefulness.
    """
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    post.upvotes += 1
    db.commit()
    return {"post_id": post_id, "upvotes": post.upvotes}

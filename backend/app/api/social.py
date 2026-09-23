"""
PERIMETER Social Platform API — Profile, Follows, Reels, DMs, Channels & Activity
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.feed import FeedPost, Story
from app.models.case import IncidentCase, TimelineEvent, LinkedPressArticle
from app.models.social import (
    Follow, FollowRequest, PostLike, PostComment, PostShare, PostSave,
    StoryView, StoryPollVote, Reel, ReelLike,
    Conversation, ConversationMember, Message,
    BroadcastChannel, ChannelMember, ChannelPost
)
from app.schemas.social import (
    UserProfileDetail, ProfileUpdateRequest, UserSearchItem,
    FollowUserResponse, FollowRequestResponse,
    CommentCreate, CommentResponse, LikeToggleResponse, SaveToggleResponse, SharePostRequest,
    StoryPollVoteRequest,
    ReelCreate, ReelResponse,
    ConversationCreate, MessageCreate, MessageResponse, ConversationResponse,
    ChannelCreate, ChannelPostCreate, ChannelPostResponse, ChannelResponse
)
from app.schemas.feed import FeedPostResponse
from app.schemas.case import CaseResponse, TimelineEntry, PressArticleLink
from app.core.security import get_current_user, get_optional_user

router = APIRouter(prefix="/social", tags=["Social Community & Safety Hub"])

def serialize_user_profile_detail(u: User, current_user_id: Optional[str], db: Session) -> UserProfileDetail:
    is_following = False
    is_pending = False
    if current_user_id and current_user_id != u.id:
        f = db.query(Follow).filter(Follow.follower_id == current_user_id, Follow.following_id == u.id).first()
        is_following = bool(f)
        if not is_following:
            req = db.query(FollowRequest).filter(
                FollowRequest.requester_id == current_user_id,
                FollowRequest.target_id == u.id,
                FollowRequest.status == "pending"
            ).first()
            is_pending = bool(req)

    # Dynamic counts from DB
    followers = db.query(Follow).filter(Follow.following_id == u.id).count()
    following = db.query(Follow).filter(Follow.follower_id == u.id).count()
    posts = db.query(FeedPost).filter(
        or_(FeedPost.author_id == u.id, FeedPost.author_name == u.name)
    ).count()

    return UserProfileDetail(
        id=u.id,
        name=u.name,
        username=u.username or f"@{u.name.lower().replace(' ', '_')}",
        email=u.email,
        phone=u.phone,
        role=u.role,
        badge_title=u.badge_title,
        avatar=u.avatar,
        bio=u.bio or "Active community safety member.",
        location=u.location or "Mumbai Metro Area",
        profile_image_url=u.profile_image_url,
        is_private=bool(u.is_private),
        followers_count=followers,
        following_count=following,
        posts_count=posts,
        is_following=is_following,
        is_follow_pending=is_pending,
        dynamic_field_1=u.dynamic_field_1,
        dynamic_field_2=u.dynamic_field_2,
        created_at=u.created_at
    )

# ----------------- 1. User Profile & Search -----------------

@router.get("/profile/me", response_model=UserProfileDetail)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return serialize_user_profile_detail(current_user, current_user.id, db)

@router.put("/profile/me", response_model=UserProfileDetail)
def update_my_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.name is not None:
        current_user.name = req.name.strip()
    if req.username is not None:
        clean_user = req.username.strip().lstrip('@')
        # check unique
        existing = db.query(User).filter(User.username == f"@{clean_user}", User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username is already taken.")
        current_user.username = f"@{clean_user}"
    if req.bio is not None:
        current_user.bio = req.bio.strip()
    if req.location is not None:
        current_user.location = req.location.strip()
    if req.phone is not None:
        current_user.phone = req.phone.strip()
    if req.profile_image_url is not None:
        current_user.profile_image_url = req.profile_image_url
    if req.avatar is not None:
        current_user.avatar = req.avatar.strip()
    if req.is_private is not None:
        current_user.is_private = req.is_private
    if req.dynamic_field_1 is not None:
        current_user.dynamic_field_1 = req.dynamic_field_1
    if req.dynamic_field_2 is not None:
        current_user.dynamic_field_2 = req.dynamic_field_2

    db.commit()
    db.refresh(current_user)
    return serialize_user_profile_detail(current_user, current_user.id, db)

@router.get("/users/{user_id}/profile", response_model=UserProfileDetail)
def get_user_profile(
    user_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    current_user_id = current_user.id if current_user else None
    return serialize_user_profile_detail(u, current_user_id, db)

@router.get("/users/search", response_model=List[UserSearchItem])
def search_users(
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    current_user_id = current_user.id if current_user else None
    query = db.query(User)
    if current_user_id:
        query = query.filter(User.id != current_user_id)

    if role and role.strip() and role.strip().lower() != 'all':
        query = query.filter(User.role == role.strip().lower())

    if q and q.strip():
        query_str = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(query_str),
                User.username.ilike(query_str),
                User.role.ilike(query_str),
                User.location.ilike(query_str),
                User.badge_title.ilike(query_str),
                User.dynamic_field_1.ilike(query_str),
                User.dynamic_field_2.ilike(query_str)
            )
        )

    users = query.order_by(User.role.asc(), User.name.asc()).limit(60).all()

    results = []
    for u in users:
        is_following = False
        if current_user_id:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user_id,
                Follow.following_id == u.id
            ).first() is not None
        followers = db.query(Follow).filter(Follow.following_id == u.id).count()

        results.append(UserSearchItem(
            id=u.id,
            name=u.name,
            username=u.username or f"@{u.name.lower().replace(' ', '_')}",
            email=u.email,
            phone=u.phone,
            role=u.role,
            badge_title=u.badge_title,
            avatar=u.avatar,
            bio=u.bio,
            location=u.location,
            followers_count=followers,
            is_following=is_following,
            dynamic_field_1=u.dynamic_field_1,
            dynamic_field_2=u.dynamic_field_2
        ))
    return results

# ----------------- 2. Follow System -----------------

@router.post("/users/{user_id}/follow", response_model=FollowUserResponse)
def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if existing_follow:
        followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
        return FollowUserResponse(
            status="success",
            message=f"You already follow {target_user.name}",
            is_following=True,
            is_pending=False,
            followers_count=followers_count
        )

    # If target account is private, create FollowRequest
    if target_user.is_private:
        existing_req = db.query(FollowRequest).filter(
            FollowRequest.requester_id == current_user.id,
            FollowRequest.target_id == user_id,
            FollowRequest.status == "pending"
        ).first()
        if not existing_req:
            req = FollowRequest(
                requester_id=current_user.id,
                target_id=user_id,
                status="pending"
            )
            db.add(req)
            db.commit()
        followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
        return FollowUserResponse(
            status="pending",
            message=f"Follow request sent to {target_user.name}",
            is_following=False,
            is_pending=True,
            followers_count=followers_count
        )

    # Standard public follow
    new_follow = Follow(
        follower_id=current_user.id,
        following_id=user_id
    )
    db.add(new_follow)
    db.commit()

    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    return FollowUserResponse(
        status="success",
        message=f"You are now following {target_user.name}",
        is_following=True,
        is_pending=False,
        followers_count=followers_count
    )

@router.post("/users/{user_id}/unfollow", response_model=FollowUserResponse)
def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    follow_rel = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if follow_rel:
        db.delete(follow_rel)
        db.commit()

    # Also clear any pending request
    req = db.query(FollowRequest).filter(
        FollowRequest.requester_id == current_user.id,
        FollowRequest.target_id == user_id
    ).first()
    if req:
        db.delete(req)
        db.commit()

    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    return FollowUserResponse(
        status="success",
        message=f"Unfollowed {target_user.name}",
        is_following=False,
        is_pending=False,
        followers_count=followers_count
    )

@router.get("/users/{user_id}/followers", response_model=List[UserSearchItem])
def get_user_followers(
    user_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    current_user_id = getattr(current_user, 'id', None)
    follows = db.query(Follow).filter(Follow.following_id == user_id).all()
    follower_ids = [f.follower_id for f in follows]
    users = db.query(User).filter(User.id.in_(follower_ids)).all() if follower_ids else []

    results = []
    for u in users:
        is_following = False
        if current_user_id:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user_id,
                Follow.following_id == u.id
            ).first() is not None
        cnt = db.query(Follow).filter(Follow.following_id == u.id).count()
        results.append(UserSearchItem(
            id=u.id,
            name=u.name,
            username=u.username or f"@{u.name.lower().replace(' ', '_')}",
            role=u.role,
            badge_title=u.badge_title,
            avatar=u.avatar,
            bio=u.bio,
            location=u.location,
            followers_count=cnt,
            is_following=is_following
        ))
    return results

@router.get("/users/{user_id}/following", response_model=List[UserSearchItem])
def get_user_following(
    user_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    current_user_id = getattr(current_user, 'id', None)
    follows = db.query(Follow).filter(Follow.follower_id == user_id).all()
    following_ids = [f.following_id for f in follows]
    users = db.query(User).filter(User.id.in_(following_ids)).all() if following_ids else []

    results = []
    for u in users:
        is_following = False
        if current_user_id:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user_id,
                Follow.following_id == u.id
            ).first() is not None
        cnt = db.query(Follow).filter(Follow.following_id == u.id).count()
        results.append(UserSearchItem(
            id=u.id,
            name=u.name,
            username=u.username or f"@{u.name.lower().replace(' ', '_')}",
            role=u.role,
            badge_title=u.badge_title,
            avatar=u.avatar,
            bio=u.bio,
            location=u.location,
            followers_count=cnt,
            is_following=is_following
        ))
    return results

@router.get("/follow-requests", response_model=List[FollowRequestResponse])
def get_follow_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requests = db.query(FollowRequest).filter(
        FollowRequest.target_id == current_user.id,
        FollowRequest.status == "pending"
    ).all()

    out = []
    for r in requests:
        sender = db.query(User).filter(User.id == r.requester_id).first()
        if sender:
            out.append(FollowRequestResponse(
                id=r.id,
                requester_id=sender.id,
                requester_name=sender.name,
                requester_username=sender.username or f"@{sender.name.lower().replace(' ', '_')}",
                requester_avatar=sender.avatar,
                requester_role=sender.role,
                created_at=r.created_at
            ))
    return out

@router.post("/follow-requests/{request_id}/respond")
def respond_follow_request(
    request_id: str,
    action: str = Query(..., pattern="^(accept|reject)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(FollowRequest).filter(
        FollowRequest.id == request_id,
        FollowRequest.target_id == current_user.id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Follow request not found.")

    if action == "accept":
        req.status = "accepted"
        # Create Follow entry
        exists = db.query(Follow).filter(
            Follow.follower_id == req.requester_id,
            Follow.following_id == current_user.id
        ).first()
        if not exists:
            db.add(Follow(follower_id=req.requester_id, following_id=current_user.id))
    else:
        req.status = "rejected"

    db.commit()
    return {"status": "success", "action": action}

# ----------------- 3. Post Likes, Comments, Shares, Saves -----------------

@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse)
def toggle_post_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    existing_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        post.upvotes = max(0, post.upvotes - 1)
        is_liked = False
    else:
        new_like = PostLike(post_id=post_id, user_id=current_user.id)
        db.add(new_like)
        post.upvotes += 1
        is_liked = True

    db.commit()
    return LikeToggleResponse(post_id=post_id, is_liked=is_liked, upvotes=post.upvotes)

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
def add_comment(
    post_id: str,
    req: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty.")

    comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_avatar=current_user.avatar,
        user_role=current_user.role,
        text=req.text.strip()
    )
    db.add(comment)
    post.comments_count += 1
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        user_name=comment.user_name,
        user_avatar=comment.user_avatar,
        user_role=comment.user_role,
        text=comment.text,
        created_at=comment.created_at
    )

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_post_comments(
    post_id: str,
    db: Session = Depends(get_db)
):
    comments = db.query(PostComment).filter(PostComment.post_id == post_id).order_by(PostComment.created_at.asc()).all()
    return [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            user_id=c.user_id,
            user_name=c.user_name,
            user_avatar=c.user_avatar,
            user_role=c.user_role,
            text=c.text,
            created_at=c.created_at
        )
        for c in comments
    ]

@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(PostComment).filter(PostComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only delete your own comments.")

    post = db.query(FeedPost).filter(FeedPost.id == comment.post_id).first()
    if post:
        post.comments_count = max(0, post.comments_count - 1)

    db.delete(comment)
    db.commit()
    return {"status": "success", "message": "Comment deleted."}

@router.post("/posts/{post_id}/share")
def share_post(
    post_id: str,
    req: SharePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    share = PostShare(post_id=post_id, user_id=current_user.id, share_target=req.target or "community_network")
    db.add(share)
    post.shares_count += 1
    db.commit()
    return {"status": "success", "post_id": post_id, "shares_count": post.shares_count}

@router.post("/posts/{post_id}/save", response_model=SaveToggleResponse)
def toggle_save_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    existing_save = db.query(PostSave).filter(
        PostSave.post_id == post_id,
        PostSave.user_id == current_user.id
    ).first()

    if existing_save:
        db.delete(existing_save)
        post.saves_count = max(0, post.saves_count - 1)
        is_saved = False
    else:
        new_save = PostSave(post_id=post_id, user_id=current_user.id)
        db.add(new_save)
        post.saves_count += 1
        is_saved = True

    db.commit()
    return SaveToggleResponse(post_id=post_id, is_saved=is_saved)

@router.post("/stories/{story_id}/vote")
def vote_story_poll(
    story_id: str,
    req: StoryPollVoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    opt = req.option.upper()
    if opt not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Invalid option. Choose A or B.")

    existing_vote = db.query(StoryPollVote).filter(
        StoryPollVote.story_id == story_id,
        StoryPollVote.user_id == current_user.id
    ).first()

    if existing_vote:
        return {"status": "already_voted", "selected": existing_vote.selected_option, "votes_a": story.poll_votes_a, "votes_b": story.poll_votes_b}

    vote = StoryPollVote(story_id=story_id, user_id=current_user.id, selected_option=opt)
    db.add(vote)
    if opt == "A":
        story.poll_votes_a += 1
    else:
        story.poll_votes_b += 1

    db.commit()
    return {"status": "success", "selected": opt, "votes_a": story.poll_votes_a, "votes_b": story.poll_votes_b}

# ----------------- 4. Activity Profiles & Case Follow-ups -----------------

@router.get("/profile/my-posts", response_model=List[FeedPostResponse])
def get_my_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.query(FeedPost).filter(
        or_(FeedPost.author_id == current_user.id, FeedPost.author_name == current_user.name)
    ).order_by(FeedPost.created_at.desc()).all()

    results = []
    for p in posts:
        is_liked = db.query(PostLike).filter(PostLike.post_id == p.id, PostLike.user_id == current_user.id).first() is not None
        is_saved = db.query(PostSave).filter(PostSave.post_id == p.id, PostSave.user_id == current_user.id).first() is not None
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
            location_name=p.location_name,
            media_url=p.media_url,
            media_type=p.media_type or "image",
            media_urls=p.media_urls,
            created_at=p.created_at,
            upvotes=p.upvotes,
            shares_count=p.shares_count,
            saves_count=p.saves_count,
            verified_by_police=p.verified_by_police,
            comments_count=p.comments_count,
            is_liked=is_liked,
            is_saved=is_saved
        ))
    return results

@router.get("/profile/my-liked-posts", response_model=List[FeedPostResponse])
def get_my_liked_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    liked = db.query(PostLike).filter(PostLike.user_id == current_user.id).all()
    post_ids = [l.post_id for l in liked]
    if not post_ids:
        return []
    posts = db.query(FeedPost).filter(FeedPost.id.in_(post_ids)).order_by(FeedPost.created_at.desc()).all()

    results = []
    for p in posts:
        is_saved = db.query(PostSave).filter(PostSave.post_id == p.id, PostSave.user_id == current_user.id).first() is not None
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
            location_name=p.location_name,
            media_url=p.media_url,
            media_type=p.media_type or "image",
            media_urls=p.media_urls,
            created_at=p.created_at,
            upvotes=p.upvotes,
            shares_count=p.shares_count,
            saves_count=p.saves_count,
            verified_by_police=p.verified_by_police,
            comments_count=p.comments_count,
            is_liked=True,
            is_saved=is_saved
        ))
    return results

@router.get("/profile/my-saved-posts", response_model=List[FeedPostResponse])
def get_my_saved_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    saved = db.query(PostSave).filter(PostSave.user_id == current_user.id).all()
    post_ids = [s.post_id for s in saved]
    if not post_ids:
        return []
    posts = db.query(FeedPost).filter(FeedPost.id.in_(post_ids)).order_by(FeedPost.created_at.desc()).all()

    results = []
    for p in posts:
        is_liked = db.query(PostLike).filter(PostLike.post_id == p.id, PostLike.user_id == current_user.id).first() is not None
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
            location_name=p.location_name,
            media_url=p.media_url,
            media_type=p.media_type or "image",
            media_urls=p.media_urls,
            created_at=p.created_at,
            upvotes=p.upvotes,
            shares_count=p.shares_count,
            saves_count=p.saves_count,
            verified_by_police=p.verified_by_police,
            comments_count=p.comments_count,
            is_liked=is_liked,
            is_saved=True
        ))
    return results

@router.get("/profile/my-cases", response_model=List[CaseResponse])
def get_my_cases(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve emergency SOS cases, help requests, and incident reports filed by this user with complete timeline.
    """
    cases = db.query(IncidentCase).filter(
        or_(
            IncidentCase.user_id == current_user.id,
            IncidentCase.victim_identifier.ilike(f"%{current_user.name}%"),
            IncidentCase.victim_identifier.ilike(f"%{current_user.id}%")
        )
    ).order_by(IncidentCase.opened_at.desc()).all()

    results = []
    for c in cases:
        events = [
            TimelineEntry(
                timestamp=e.timestamp,
                title=e.title,
                description=e.description,
                actor_role=e.actor_role,
                actor_name=e.actor_name
            )
            for e in sorted(c.timeline_events, key=lambda x: x.timestamp)
        ]
        articles = [
            PressArticleLink(
                article_id=a.article_id,
                title=a.title,
                outlet=a.outlet,
                journalist_name=a.journalist_name,
                url=a.url,
                published_at=a.published_at
            )
            for a in c.linked_press_reports
        ]
        results.append(CaseResponse(
            case_id=c.case_id,
            title=c.title,
            victim_identifier=c.victim_identifier,
            status=c.status,
            priority=c.priority,
            location=c.location,
            opened_at=c.opened_at,
            assigned_precinct=c.assigned_precinct,
            timeline=events,
            linked_press_reports=articles
        ))
    return results

# ----------------- 5. Reels Video Hub -----------------

@router.get("/reels", response_model=List[ReelResponse])
def get_reels(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reels = db.query(Reel).order_by(Reel.created_at.desc()).all()
    results = []
    for r in reels:
        is_liked = db.query(ReelLike).filter(ReelLike.reel_id == r.id, ReelLike.user_id == current_user.id).first() is not None
        results.append(ReelResponse(
            id=r.id,
            author_id=r.author_id,
            author_name=r.author_name,
            author_avatar=r.author_avatar,
            author_role=r.author_role,
            caption=r.caption,
            video_url=r.video_url,
            thumbnail_url=r.thumbnail_url,
            audio_title=r.audio_title,
            duration_seconds=r.duration_seconds,
            likes_count=r.likes_count,
            comments_count=r.comments_count,
            is_liked=is_liked,
            created_at=r.created_at
        ))
    return results

@router.post("/reels", response_model=ReelResponse)
def create_reel(
    req: ReelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not req.video_url:
        raise HTTPException(status_code=400, detail="Video URL is required.")

    dur = min(90, max(5, req.duration_seconds or 30))
    reel = Reel(
        author_id=current_user.id,
        author_name=current_user.name,
        author_avatar=current_user.avatar,
        author_role=current_user.role,
        caption=req.caption.strip(),
        video_url=req.video_url.strip(),
        thumbnail_url=req.thumbnail_url,
        audio_title=req.audio_title or "Original Safety Audio — Perimeter Sound",
        duration_seconds=dur,
        likes_count=0,
        comments_count=0
    )
    db.add(reel)
    db.commit()
    db.refresh(reel)

    return ReelResponse(
        id=reel.id,
        author_id=reel.author_id,
        author_name=reel.author_name,
        author_avatar=reel.author_avatar,
        author_role=reel.author_role,
        caption=reel.caption,
        video_url=reel.video_url,
        thumbnail_url=reel.thumbnail_url,
        audio_title=reel.audio_title,
        duration_seconds=reel.duration_seconds,
        likes_count=reel.likes_count,
        comments_count=reel.comments_count,
        is_liked=False,
        created_at=reel.created_at
    )

@router.post("/reels/{reel_id}/like")
def toggle_reel_like(
    reel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reel = db.query(Reel).filter(Reel.id == reel_id).first()
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found.")

    existing_like = db.query(ReelLike).filter(
        ReelLike.reel_id == reel_id,
        ReelLike.user_id == current_user.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        reel.likes_count = max(0, reel.likes_count - 1)
        is_liked = False
    else:
        new_like = ReelLike(reel_id=reel_id, user_id=current_user.id)
        db.add(new_like)
        reel.likes_count += 1
        is_liked = True

    db.commit()
    return {"reel_id": reel_id, "is_liked": is_liked, "likes_count": reel.likes_count}

# ----------------- 6. Direct Messages -----------------

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(ConversationMember).filter(ConversationMember.user_id == current_user.id).all()
    conv_ids = [m.conversation_id for m in memberships]
    if not conv_ids:
        return []

    convs = db.query(Conversation).filter(Conversation.id.in_(conv_ids)).order_by(Conversation.updated_at.desc()).all()
    results = []
    for c in convs:
        # find other member
        other_member = db.query(ConversationMember).filter(
            ConversationMember.conversation_id == c.id,
            ConversationMember.user_id != current_user.id
        ).first()

        recip_user = None
        if other_member:
            recip_user = db.query(User).filter(User.id == other_member.user_id).first()

        # last message
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()

        results.append(ConversationResponse(
            id=c.id,
            title=c.title or (recip_user.name if recip_user else "Direct Conversation"),
            is_group=c.is_group,
            recipient_id=recip_user.id if recip_user else None,
            recipient_name=recip_user.name if recip_user else "Perimeter Contact",
            recipient_avatar=recip_user.avatar if recip_user else "P",
            recipient_role=recip_user.role if recip_user else "user",
            last_message=last_msg.text if last_msg else "No messages yet.",
            last_message_time=last_msg.created_at if last_msg else c.created_at,
            unread_count=0,
            created_at=c.created_at
        ))
    return results

@router.post("/conversations", response_model=ConversationResponse)
def get_or_create_conversation(
    req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself.")

    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found.")

    # Check existing conversation between both
    my_conv_ids = [m.conversation_id for m in db.query(ConversationMember).filter(ConversationMember.user_id == current_user.id).all()]
    existing_conv = db.query(ConversationMember).filter(
        ConversationMember.conversation_id.in_(my_conv_ids),
        ConversationMember.user_id == req.recipient_id
    ).first()

    if existing_conv:
        c = db.query(Conversation).filter(Conversation.id == existing_conv.conversation_id).first()
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        return ConversationResponse(
            id=c.id,
            title=recipient.name,
            is_group=False,
            recipient_id=recipient.id,
            recipient_name=recipient.name,
            recipient_avatar=recipient.avatar,
            recipient_role=recipient.role,
            last_message=last_msg.text if last_msg else "Started conversation",
            last_message_time=last_msg.created_at if last_msg else c.created_at,
            unread_count=0,
            created_at=c.created_at
        )

    # Create new conversation
    new_conv = Conversation(title=f"{current_user.name} & {recipient.name}", is_group=False)
    db.add(new_conv)
    db.flush()

    m1 = ConversationMember(conversation_id=new_conv.id, user_id=current_user.id)
    m2 = ConversationMember(conversation_id=new_conv.id, user_id=recipient.id)
    db.add_all([m1, m2])
    db.commit()
    db.refresh(new_conv)

    return ConversationResponse(
        id=new_conv.id,
        title=recipient.name,
        is_group=False,
        recipient_id=recipient.id,
        recipient_name=recipient.name,
        recipient_avatar=recipient.avatar,
        recipient_role=recipient.role,
        last_message="Conversation created",
        last_message_time=new_conv.created_at,
        unread_count=0,
        created_at=new_conv.created_at
    )

@router.get("/conversations/{conv_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify membership
    member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conv_id,
        ConversationMember.user_id == current_user.id
    ).first()
    if not member and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not a member of this conversation.")

    messages = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.asc()).all()
    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            sender_name=m.sender_name,
            sender_avatar=m.sender_avatar,
            text=m.text,
            media_url=m.media_url,
            is_read=m.is_read,
            created_at=m.created_at
        )
        for m in messages
    ]

@router.post("/conversations/{conv_id}/messages", response_model=MessageResponse)
def send_message(
    conv_id: str,
    req: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify membership
    member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conv_id,
        ConversationMember.user_id == current_user.id
    ).first()
    if not member and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not a member of this conversation.")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")

    msg = Message(
        conversation_id=conv_id,
        sender_id=current_user.id,
        sender_name=current_user.name,
        sender_avatar=current_user.avatar,
        text=req.text.strip(),
        media_url=req.media_url,
        is_read=False
    )
    db.add(msg)

    # update conversation updated_at
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if conv:
        conv.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(msg)

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender_name=msg.sender_name,
        sender_avatar=msg.sender_avatar,
        text=msg.text,
        media_url=msg.media_url,
        is_read=msg.is_read,
        created_at=msg.created_at
    )

# ----------------- 7. Broadcast Channels -----------------

@router.get("/channels", response_model=List[ChannelResponse])
def get_broadcast_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channels = db.query(BroadcastChannel).order_by(BroadcastChannel.created_at.desc()).all()
    results = []
    for ch in channels:
        is_sub = db.query(ChannelMember).filter(
            ChannelMember.channel_id == ch.id,
            ChannelMember.user_id == current_user.id
        ).first() is not None

        posts = db.query(ChannelPost).filter(ChannelPost.channel_id == ch.id).order_by(ChannelPost.created_at.desc()).limit(3).all()
        post_responses = [
            ChannelPostResponse(
                id=p.id,
                channel_id=p.channel_id,
                author_name=p.author_name,
                title=p.title,
                content=p.content,
                media_url=p.media_url,
                created_at=p.created_at
            )
            for p in posts
        ]

        results.append(ChannelResponse(
            id=ch.id,
            creator_id=ch.creator_id,
            creator_name=ch.creator_name,
            creator_role=ch.creator_role,
            name=ch.name,
            description=ch.description,
            category=ch.category,
            avatar=ch.avatar,
            subscriber_count=ch.subscriber_count,
            is_subscribed=is_sub,
            recent_posts=post_responses,
            created_at=ch.created_at
        ))
    return results

@router.post("/channels", response_model=ChannelResponse)
def create_broadcast_channel(
    req: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["police", "journalist", "admin", "volunteer"]:
        raise HTTPException(
            status_code=403,
            detail="Only verified officials, police, journalists, and admins can create public broadcast channels."
        )

    channel = BroadcastChannel(
        creator_id=current_user.id,
        creator_name=current_user.name,
        creator_role=current_user.role,
        name=req.name.strip(),
        description=req.description.strip(),
        category=req.category or "SAFETY_ALERTS",
        avatar=req.avatar or "📢",
        subscriber_count=1
    )
    db.add(channel)
    db.flush()

    # Creator auto-subscribes
    db.add(ChannelMember(channel_id=channel.id, user_id=current_user.id))
    db.commit()
    db.refresh(channel)

    return ChannelResponse(
        id=channel.id,
        creator_id=channel.creator_id,
        creator_name=channel.creator_name,
        creator_role=channel.creator_role,
        name=channel.name,
        description=channel.description,
        category=channel.category,
        avatar=channel.avatar,
        subscriber_count=1,
        is_subscribed=True,
        recent_posts=[],
        created_at=channel.created_at
    )

@router.post("/channels/{channel_id}/subscribe")
def toggle_channel_subscription(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channel = db.query(BroadcastChannel).filter(BroadcastChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    sub = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user.id
    ).first()

    if sub:
        db.delete(sub)
        channel.subscriber_count = max(0, channel.subscriber_count - 1)
        is_sub = False
    else:
        db.add(ChannelMember(channel_id=channel_id, user_id=current_user.id))
        channel.subscriber_count += 1
        is_sub = True

    db.commit()
    return {"channel_id": channel_id, "is_subscribed": is_sub, "subscriber_count": channel.subscriber_count}

@router.get("/channels/{channel_id}/posts", response_model=List[ChannelPostResponse])
def get_channel_posts(
    channel_id: str,
    db: Session = Depends(get_db)
):
    posts = db.query(ChannelPost).filter(ChannelPost.channel_id == channel_id).order_by(ChannelPost.created_at.desc()).all()
    return [
        ChannelPostResponse(
            id=p.id,
            channel_id=p.channel_id,
            author_name=p.author_name,
            title=p.title,
            content=p.content,
            media_url=p.media_url,
            created_at=p.created_at
        )
        for p in posts
    ]

@router.post("/channels/{channel_id}/posts", response_model=ChannelPostResponse)
def publish_channel_post(
    channel_id: str,
    req: ChannelPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channel = db.query(BroadcastChannel).filter(BroadcastChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    if channel.creator_id != current_user.id and current_user.role not in ["admin", "police"]:
        raise HTTPException(status_code=403, detail="Only channel creators and authorized police/admins can broadcast to this channel.")

    post = ChannelPost(
        channel_id=channel_id,
        author_name=current_user.name,
        title=req.title.strip(),
        content=req.content.strip(),
        media_url=req.media_url
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return ChannelPostResponse(
        id=post.id,
        channel_id=post.channel_id,
        author_name=post.author_name,
        title=post.title,
        content=post.content,
        media_url=post.media_url,
        created_at=post.created_at
    )

"""
PERIMETER Platform — End-to-End Social Safety & Core Integration Test Suite
"""
import sys
import os
import uuid
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.models.user import User
from app.models.sos import SOSIncident, Responder
from app.models.feed import FeedPost, Story
from app.models.case import IncidentCase, TimelineEvent

from app.api.auth import register_user, login_user, get_all_users
from app.api.feed import (
    get_feed_posts, create_feed_post, upvote_post, get_stories, create_story
)
from app.api.social import (
    get_my_profile, update_my_profile, search_users,
    follow_user, unfollow_user, get_user_followers, get_user_following,
    toggle_post_like, add_comment, share_post, toggle_save_post,
    vote_story_poll, get_reels, create_reel, toggle_reel_like,
    get_or_create_conversation, send_message, get_conversation_messages,
    get_broadcast_channels, create_broadcast_channel, toggle_channel_subscription,
    get_my_posts, get_my_liked_posts, get_my_saved_posts, get_my_cases
)
from app.api.sos import trigger_sos, get_active_incidents, respond_to_incident, resolve_incident
from app.api.case import get_all_cases, get_case_by_id, add_timeline_event
from app.api.admin import get_admin_stats, get_system_status

from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.schemas.feed import FeedPostCreate, StoryCreate
from app.schemas.social import (
    ProfileUpdateRequest, CommentCreate, SharePostRequest, StoryPollVoteRequest,
    ReelCreate, ConversationCreate, MessageCreate, ChannelCreate
)
from app.schemas.sos import SOSTriggerRequest, LocationCoords
from app.schemas.case import TimelineEntry
from app.core.security import decode_access_token, verify_password

def run_tests():
    print("=" * 65)
    print("🛡️  RUNNING PERIMETER SOCIAL SAFETY INTEGRATION TESTS")
    print("=" * 65)

    # Initialize DB
    init_db()
    db = SessionLocal()

    try:
        # 1. Test Seeded Personas & Database Connection
        users = get_all_users(db)
        assert len(users) >= 5, f"Expected at least 5 seeded users, got {len(users)}"
        roles = {u.role for u in users}
        assert {"user", "volunteer", "police", "journalist", "admin"}.issubset(roles)
        print(f"✅ [1/15] Database Initialization & Seeded Roles: OK ({len(users)} users across 5 roles)")

        # 2. Test Register New Citizen User & Persistent JWT Generation
        unique_email = f"citizen.{uuid.uuid4().hex[:6]}@perimeter.org"
        reg_req = UserRegisterRequest(
            name="Ananya Sen",
            username=f"@ananya_{uuid.uuid4().hex[:4]}",
            email=unique_email,
            phone="+91 98765 43210",
            password="SecurePassword2026!",
            role="user",
            bio="Safe walks advocate in Mumbai West",
            location="Bandra West Sector 3",
            dynamic_field_1="+91 99999 00000",
            dynamic_field_2="Bandra West Sector 3"
        )
        reg_res = register_user(reg_req, db)
        assert reg_res.access_token is not None
        assert reg_res.user.email == unique_email
        token = reg_res.access_token
        user_id = reg_res.user.id
        
        # Load user db object
        current_user = db.query(User).filter(User.id == user_id).first()

        # Verify decoded JWT payload
        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") == user_id
        assert payload.get("role") == "user"
        print(f"✅ [2/15] One-Time Registration & Signed JWT Token: OK (User ID: {user_id})")

        # 3. Test Profile Fetch & Update
        prof = get_my_profile(current_user=current_user, db=db)
        assert prof.name == "Ananya Sen"
        
        up_req = ProfileUpdateRequest(
            bio="Certified Community Safety Leader | Mumbai West",
            location="Bandra West, Mumbai",
            is_private=False
        )
        up_prof = update_my_profile(req=up_req, current_user=current_user, db=db)
        assert up_prof.bio == "Certified Community Safety Leader | Mumbai West"
        print("✅ [3/15] Profile Metadata & Bio/Location Updates: OK")

        # 4. Test Search Users & Follow / Unfollow System
        search_res = search_users(q="aarohi", current_user=current_user, db=db)
        assert len(search_res) >= 1
        target_user = search_res[0]
        
        fol_res = follow_user(user_id=target_user.id, current_user=current_user, db=db)
        assert fol_res.is_following is True
        
        followers = get_user_followers(user_id=target_user.id, current_user=current_user, db=db)
        assert any(f.id == user_id for f in followers)
        
        following = get_user_following(user_id=user_id, current_user=current_user, db=db)
        assert any(f.id == target_user.id for f in following)
        print(f"✅ [4/15] Social Search & Follow Network: OK (Followed {target_user.name})")

        # 5. Test Safety Feed (Create, Like, Comment, Share, Save)
        post_req = FeedPostCreate(
            author_id=user_id,
            author_name="Ananya Sen",
            author_role="user",
            title="Lit Walking Corridor Verified",
            content="Street lights are fully functional on 14th Road. Verified with volunteers.",
            tag="SAFE_ROUTE",
            location_name="14th Road, Bandra West"
        )
        created_post = create_feed_post(req=post_req, current_user=current_user, db=db)
        assert created_post.id is not None

        # Like
        like_res = toggle_post_like(post_id=created_post.id, current_user=current_user, db=db)
        assert like_res.is_liked is True

        # Comment
        comment_res = add_comment(
            post_id=created_post.id,
            req=CommentCreate(text="Verified! Walking this route right now."),
            current_user=current_user,
            db=db
        )
        assert comment_res.text == "Verified! Walking this route right now."

        # Share & Save
        share_res = share_post(
            post_id=created_post.id,
            req=SharePostRequest(target="community_network"),
            current_user=current_user,
            db=db
        )
        assert share_res["shares_count"] >= 1

        save_res = toggle_save_post(post_id=created_post.id, current_user=current_user, db=db)
        assert save_res.is_saved is True
        print(f"✅ [5/15] Feed Post Interactions (Like, Comment, Share, Save): OK (Post: {created_post.id})")

        # 6. Test 24-Hour Stories & Interactive Polls
        story_req = StoryCreate(
            author_id=user_id,
            author_name="Ananya Sen",
            author_role="user",
            author_avatar="AS",
            caption="Safely reached home via Bandra Station Corridor! How safe is your commute?",
            tag="SAFE_STATUS",
            poll_question="Are you walking alone tonight?",
            poll_option_a="Yes, tracking on app",
            poll_option_b="No, with a buddy"
        )
        created_story = create_story(req=story_req, current_user=current_user, db=db)
        assert created_story.id is not None
        assert created_story.poll_question == "Are you walking alone tonight?"

        # Vote in story poll
        vote_res = vote_story_poll(
            story_id=created_story.id,
            req=StoryPollVoteRequest(option="A"),
            current_user=current_user,
            db=db
        )
        assert vote_res["status"] == "success"
        print("✅ [6/15] 24h Safety Stories with Interactive Polls: OK")

        # 7. Test Reels Safety Video Flow
        reel_req = ReelCreate(
            caption="Highlights of brightly lit safe transit route from Platform 1 to Linking Road.",
            video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            duration_seconds=30
        )
        created_reel = create_reel(req=reel_req, current_user=current_user, db=db)
        assert created_reel.id is not None

        reel_like = toggle_reel_like(reel_id=created_reel.id, current_user=current_user, db=db)
        assert reel_like["is_liked"] is True
        print("✅ [7/15] Safety Reels & Video Sharing: OK")

        # 8. Test Direct Messages (DMs)
        conv = get_or_create_conversation(
            req=ConversationCreate(recipient_id=target_user.id),
            current_user=current_user,
            db=db
        )
        assert conv.id is not None
        conv_id = conv.id

        msg = send_message(
            conv_id=conv_id,
            req=MessageCreate(text="Hey Aarohi, are you free for the community night walk tomorrow?"),
            current_user=current_user,
            db=db
        )
        assert msg.text.startswith("Hey Aarohi")

        msgs = get_conversation_messages(conv_id=conv_id, current_user=current_user, db=db)
        assert len(msgs) >= 1
        print(f"✅ [8/15] Direct Messages (Conversations & Chat): OK (Conv: {conv_id})")

        # 9. Test Broadcast Channels
        channels = get_broadcast_channels(current_user=current_user, db=db)
        assert len(channels) >= 1
        first_channel = channels[0]

        sub_res = toggle_channel_subscription(channel_id=first_channel.id, current_user=current_user, db=db)
        assert isinstance(sub_res["is_subscribed"], bool)
        print(f"✅ [9/15] Broadcast Safety Channels Subscription: OK (Channel: {first_channel.name})")

        # 10. Test Emergency SOS Trigger & Auto Case Provisioning
        sos_req = SOSTriggerRequest(
            user_name="Ananya Sen",
            user_id=user_id,
            phone="+91 98765 43210",
            trigger_type="SHAKE_MOTION",
            severity="CRITICAL",
            location=LocationCoords(
                latitude=19.0760,
                longitude=72.8777,
                accuracy_meters=8.0,
                address="SV Road, Near Bandra Metro Pillar #42"
            ),
            notes="Hands-free shake motion SOS triggered by citizen."
        )
        sos_res = trigger_sos(sos_req, db)
        inc_id = sos_res["incident_id"]
        case_id = sos_res["case_id"]
        assert inc_id.startswith("SOS-2026-")
        assert case_id.startswith("CAS-2026-")
        assert sos_res["status"] == "ACTIVE_DISPATCH"
        print(f"✅ [10/15] Emergency SOS Trigger & Auto Case Creation: OK (SOS: {inc_id} -> Case: {case_id})")

        # 11. Test Volunteer Dispatch Response & Police Resolution
        active_incidents = get_active_incidents(db)
        assert any(i["incident_id"] == inc_id for i in active_incidents)

        resp_res = respond_to_incident(
            incident_id=inc_id,
            responder_id="vol_001",
            responder_name="Priya Deshmukh",
            role="volunteer",
            db=db
        )
        assert resp_res["status"] == "success"

        # Police resolves incident
        resolve_res = resolve_incident(
            incident_id=inc_id,
            resolved_by="Inspector K. Patil",
            notes="Citizen secured and escort provided.",
            db=db
        )
        assert resolve_res["status"] == "success"

        # Verify Case was updated to RESOLVED with timeline
        case_obj = get_case_by_id(case_id, db)
        assert case_obj.status == "RESOLVED"
        assert len(case_obj.timeline) >= 3
        print("✅ [11/15] Responder Dispatch & Case Resolution Lifecycle: OK")

        # 12. Test Profile Activity Queries (My Posts, Liked Posts, Saved Posts, My Cases)
        my_posts = get_my_posts(current_user=current_user, db=db)
        assert len(my_posts) >= 1
        assert any(p.id == created_post.id for p in my_posts)

        liked_posts = get_my_liked_posts(current_user=current_user, db=db)
        assert len(liked_posts) >= 1

        saved_posts = get_my_saved_posts(current_user=current_user, db=db)
        assert len(saved_posts) >= 1

        my_cases = get_my_cases(current_user=current_user, db=db)
        assert len(my_cases) >= 1
        assert any(c.case_id == case_id for c in my_cases)
        print("✅ [12/15] Profile Activities Feeds (My Posts, Likes, Saves, My Cases): OK")

        # 13. Test Feed Post Filter & Category Query
        all_posts = get_feed_posts(category="ALL", db=db)
        assert len(all_posts) >= 2
        
        user_posts = get_feed_posts(category="SAFE_ROUTE", db=db)
        assert any(p.id == created_post.id for p in user_posts)
        print("✅ [13/15] Categorized Safety Feed Filtering: OK")

        # 14. Test Seeded Persona Auth
        login_req = UserLoginRequest(
            identity="aarohi.sharma@perimeter.org",
            password="password123"
        )
        login_res = login_user(login_req, db)
        assert login_res.access_token is not None
        assert login_res.user.name == "Aarohi Sharma"
        print("✅ [14/15] Persona Verification & Decryption: OK")

        # 15. Test Admin Stats & System Health
        stats = get_admin_stats(db)
        assert stats.total_users >= 6
        assert stats.users_by_role["user"] >= 2
        assert stats.total_cases >= 2

        sys_status = get_system_status(db)
        assert sys_status.status == "OPERATIONAL"
        print(f"✅ [15/15] Admin Platform Metrics & System Overview: OK ({stats.total_users} Users, {stats.total_cases} Cases, {stats.total_feed_posts} Posts)")

        print("=" * 65)
        print("🎉 ALL 15 INTEGRATION SUITES PASSED WITH 100% SUCCESS!")
        print("=" * 65)

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()

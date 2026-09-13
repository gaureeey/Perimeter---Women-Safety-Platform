from app.db.session import engine, Base, SessionLocal
from app.models.user import User
from app.models.sos import SOSIncident, Responder
from app.models.feed import FeedPost, Story
from app.models.case import IncidentCase, TimelineEvent, LinkedPressArticle
from app.models.social import (
    Follow, FollowRequest, PostLike, PostComment, PostShare, PostSave,
    StoryView, StoryPollVote, Reel, ReelLike,
    Conversation, ConversationMember, Message,
    BroadcastChannel, ChannelMember, ChannelPost
)
from app.core.security import get_password_hash
from datetime import datetime, timedelta

def init_db():
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed initial test personas if database is empty
        if db.query(User).count() == 0:
            demo_users = [
                User(
                    id="usr_001",
                    name="Aarohi Sharma",
                    username="@aarohi_sharma",
                    email="aarohi.sharma@perimeter.org",
                    phone="+91 98200 12345",
                    password=get_password_hash("password123"),
                    role="user",
                    badge_title="Citizen User",
                    avatar="AS",
                    bio="Software engineer & night commuter. Active safety contributor in Bandra West.",
                    location="Bandra West, Mumbai",
                    followers_count=2,
                    following_count=3,
                    posts_count=2,
                    dynamic_field_1="+91 98200 12345",
                    dynamic_field_2="Bandra West, Mumbai"
                ),
                User(
                    id="vol_001",
                    name="Priya Deshmukh",
                    username="@priya_responder",
                    email="priya.deshmukh@volunteers.perimeter.org",
                    phone="+91 98300 67890",
                    password=get_password_hash("password123"),
                    role="volunteer",
                    badge_title="Verified Responder",
                    avatar="PD",
                    bio="Certified Emergency First Responder & Night Escort Volunteer.",
                    location="Sector 4 - Central Zone",
                    followers_count=5,
                    following_count=1,
                    posts_count=3,
                    dynamic_field_1="VOL-MH-2026-089",
                    dynamic_field_2="Sector 4 - Central Zone"
                ),
                User(
                    id="pol_001",
                    name="Inspector K. Patil",
                    username="@inspector_patil",
                    email="patil.k@police.gov.in",
                    phone="+91 98111 22334",
                    password=get_password_hash("password123"),
                    role="police",
                    badge_title="City Police Command",
                    avatar="IP",
                    bio="Mumbai Police Women Safety Cell & Quick Response Unit In-charge.",
                    location="Central Police Precinct #01",
                    followers_count=18,
                    following_count=0,
                    posts_count=4,
                    dynamic_field_1="MH-CID-4521",
                    dynamic_field_2="Central Police Precinct #01"
                ),
                User(
                    id="prs_001",
                    name="Rhea Nair",
                    username="@rhea_reports",
                    email="rhea.nair@press.perimeter.org",
                    phone="+91 98444 55667",
                    password=get_password_hash("password123"),
                    role="journalist",
                    badge_title="Press Reporter",
                    avatar="RN",
                    bio="Senior Investigative Journalist focusing on urban safety & public transit accountability.",
                    location="The Deccan Herald Bureau",
                    followers_count=12,
                    following_count=4,
                    posts_count=2,
                    dynamic_field_1="PID-2026-044",
                    dynamic_field_2="The Deccan Herald"
                ),
                User(
                    id="adm_001",
                    name="Platform Administrator",
                    username="@perimeter_root",
                    email="admin.root@perimeter.org",
                    phone="+91 98000 00000",
                    password=get_password_hash("password123"),
                    role="admin",
                    badge_title="Super Administrator",
                    avatar="SA",
                    bio="Perimeter Core Infrastructure Operations & Verification Authority.",
                    location="PERIMETER HQ",
                    followers_count=40,
                    following_count=0,
                    posts_count=0,
                    dynamic_field_1="ADM-ROOT-001",
                    dynamic_field_2="PERIMETER Central Operations"
                )
            ]
            db.add_all(demo_users)
            db.flush()

            # Seed Follow relationships
            demo_follows = [
                Follow(follower_id="usr_001", following_id="vol_001"),
                Follow(follower_id="usr_001", following_id="pol_001"),
                Follow(follower_id="usr_001", following_id="prs_001"),
                Follow(follower_id="vol_001", following_id="pol_001"),
                Follow(follower_id="prs_001", following_id="pol_001"),
                Follow(follower_id="prs_001", following_id="vol_001")
            ]
            db.add_all(demo_follows)

        # 2. Seed initial feed posts
        if db.query(FeedPost).count() == 0:
            demo_posts = [
                FeedPost(
                    id="post_001",
                    author_id="pol_001",
                    author_name="Inspector K. Patil",
                    author_role="police",
                    author_badge="City Police Command",
                    author_avatar="IP",
                    title="Verified Safe Corridor: Linking Road to Bandra Station",
                    content="Special Women Safety night patrol unit dispatched on Linking Road stretch between 8 PM to 4 AM. CCTV surveillance active along all 12 junction points.",
                    tag="POLICE_NOTICE",
                    location_name="Linking Road Corridor, Bandra",
                    media_url="https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=800&q=80",
                    media_type="image",
                    upvotes=42,
                    shares_count=14,
                    saves_count=19,
                    verified_by_police=True,
                    comments_count=2
                ),
                FeedPost(
                    id="post_002",
                    author_id="vol_001",
                    author_name="Priya Deshmukh",
                    author_role="volunteer",
                    author_badge="Verified Responder",
                    author_avatar="PD",
                    title="Caution: Street Light Malfunction near Park Lane",
                    content="Street lights are unlit near the park exit. Volunteers patrolling the stretch until municipal repairs are completed. Use the Metro Gate 2 route instead.",
                    tag="HAZARD_ALERT",
                    location_name="Park Lane Sector 4",
                    media_url="https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=800&q=80",
                    media_type="image",
                    upvotes=29,
                    shares_count=8,
                    saves_count=11,
                    verified_by_police=False,
                    comments_count=1
                ),
                FeedPost(
                    id="post_003",
                    author_id="prs_001",
                    author_name="Rhea Nair",
                    author_role="journalist",
                    author_badge="Press Reporter",
                    author_avatar="RN",
                    title="Press Investigation: Night Transit Safety Audit Released",
                    content="Investigation into last-mile bus & auto connectivity around metro hubs shows 94% improved response speed after geofence dispatch integration.",
                    tag="PRESS_REPORT",
                    location_name="Metro Line 3 Interchanges",
                    media_url="https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=800&q=80",
                    media_type="image",
                    upvotes=56,
                    shares_count=22,
                    saves_count=35,
                    verified_by_police=False,
                    comments_count=1
                ),
                FeedPost(
                    id="post_004",
                    author_id="usr_001",
                    author_name="Aarohi Sharma",
                    author_role="user",
                    author_badge="Citizen User",
                    author_avatar="AS",
                    title="Late Night Walking Group Formed for Bandra West",
                    content="We have started a community walking buddy group from Bandra Station to Hill Road between 10 PM and 1 AM. All verified female commuters are welcome!",
                    tag="COMMUNITY_UPDATE",
                    location_name="Hill Road Junction",
                    media_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&q=80",
                    media_type="image",
                    upvotes=34,
                    shares_count=12,
                    saves_count=16,
                    verified_by_police=False,
                    comments_count=1
                )
            ]
            db.add_all(demo_posts)
            db.flush()

            # Seed comments
            demo_comments = [
                PostComment(
                    id="cmt_001",
                    post_id="post_001",
                    user_id="usr_001",
                    user_name="Aarohi Sharma",
                    user_avatar="AS",
                    user_role="user",
                    text="Thank you Inspector Patil! This route feels much safer now."
                ),
                PostComment(
                    id="cmt_002",
                    post_id="post_001",
                    user_id="vol_001",
                    user_name="Priya Deshmukh",
                    user_avatar="PD",
                    user_role="volunteer",
                    text="Our volunteer patrol team is also stationed at Pillar 18 to assist commuters."
                ),
                PostComment(
                    id="cmt_003",
                    post_id="post_002",
                    user_id="usr_001",
                    user_name="Aarohi Sharma",
                    user_avatar="AS",
                    user_role="user",
                    text="Thanks for the alert! Avoided the park lane today."
                ),
                PostComment(
                    id="cmt_004",
                    post_id="post_004",
                    user_id="vol_001",
                    user_name="Priya Deshmukh",
                    user_avatar="PD",
                    user_role="volunteer",
                    text="Great initiative Aarohi! Adding this to our Sector 4 safety network."
                )
            ]
            db.add_all(demo_comments)

        # 3. Seed initial Stories with Polls
        if db.query(Story).count() == 0:
            demo_stories = [
                Story(
                    id="story_001",
                    author_id="usr_001",
                    author_name="Aarohi Sharma",
                    author_role="user",
                    author_avatar="AS",
                    caption="Walking home via Linking Road safe corridor. Brightly lit and verified!",
                    tag="SAFE_STATUS",
                    bg_gradient="linear-gradient(135deg, #FF5A5F, #8B5CF6)",
                    location_tag="Linking Road, Bandra",
                    poll_question="Is your route home lit tonight?",
                    poll_option_a="Yes, well-lit",
                    poll_option_b="No, need escort",
                    poll_votes_a=18,
                    poll_votes_b=4,
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                ),
                Story(
                    id="story_002",
                    author_id="vol_001",
                    author_name="Priya Deshmukh",
                    author_role="volunteer",
                    author_avatar="PD",
                    caption="Volunteer Sector 4 Patrol active. 4 volunteers on duty near station.",
                    tag="PATROL_ACTIVE",
                    bg_gradient="linear-gradient(135deg, #D97706, #0F6E6E)",
                    location_tag="Bandra Station West",
                    poll_question="Need volunteer buddy escort?",
                    poll_option_a="I'm good",
                    poll_option_b="Request buddy",
                    poll_votes_a=24,
                    poll_votes_b=6,
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                ),
                Story(
                    id="story_003",
                    author_id="pol_001",
                    author_name="Inspector K. Patil",
                    author_role="police",
                    author_avatar="IP",
                    caption="City Police: PCR Vans #04 and #09 stationed at Metro Gate 2 all night.",
                    tag="POLICE_ALERT",
                    bg_gradient="linear-gradient(135deg, #1E3A8A, #3B82F6)",
                    location_tag="Metro Gate 2 Interchange",
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                ),
                Story(
                    id="story_004",
                    author_id="prs_001",
                    author_name="Rhea Nair",
                    author_role="journalist",
                    author_avatar="RN",
                    caption="Press Desk: Verified safety audit published with citywide timeline.",
                    tag="PRESS_UPDATE",
                    bg_gradient="linear-gradient(135deg, #0F6E6E, #2DD4BF)",
                    location_tag="Press Information Bureau",
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                )
            ]
            db.add_all(demo_stories)

        # 4. Seed initial Reels
        if db.query(Reel).count() == 0:
            demo_reels = [
                Reel(
                    id="reel_001",
                    author_id="vol_001",
                    author_name="Priya Deshmukh",
                    author_avatar="PD",
                    author_role="volunteer",
                    caption="3 Essential Self-Defense & Spatial Awareness Tips for Night Commuters 🛡️",
                    video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                    thumbnail_url="https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&q=80",
                    audio_title="Urban Safety Guide #01",
                    duration_seconds=45,
                    likes_count=89,
                    comments_count=14
                ),
                Reel(
                    id="reel_002",
                    author_id="pol_001",
                    author_name="Inspector K. Patil",
                    author_avatar="IP",
                    author_role="police",
                    caption="How Perimeter 5km Geofence Instant Dispatch works in under 3 minutes 🚔",
                    video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                    thumbnail_url="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&q=80",
                    audio_title="Police Official Alert Feed",
                    duration_seconds=58,
                    likes_count=142,
                    comments_count=23
                )
            ]
            db.add_all(demo_reels)

        # 5. Seed initial Direct Messages
        if db.query(Conversation).count() == 0:
            conv = Conversation(
                id="conv_demo_01",
                title="Aarohi & Priya",
                is_group=False
            )
            db.add(conv)
            db.flush()

            m1 = ConversationMember(conversation_id="conv_demo_01", user_id="usr_001")
            m2 = ConversationMember(conversation_id="conv_demo_01", user_id="vol_001")
            db.add_all([m1, m2])

            msg1 = Message(
                id="msg_001",
                conversation_id="conv_demo_01",
                sender_id="usr_001",
                sender_name="Aarohi Sharma",
                sender_avatar="AS",
                text="Hi Priya! Are volunteer escorts available around 11:30 PM at Bandra Station?",
                is_read=True
            )
            msg2 = Message(
                id="msg_002",
                conversation_id="conv_demo_01",
                sender_id="vol_001",
                sender_name="Priya Deshmukh",
                sender_avatar="PD",
                text="Hello Aarohi! Yes, Unit 4 is stationed at Exit 2 until 1 AM. Just tap SOS or request buddy!",
                is_read=True
            )
            db.add_all([msg1, msg2])

        # 6. Seed Broadcast Channels
        if db.query(BroadcastChannel).count() == 0:
            ch1 = BroadcastChannel(
                id="chan_001",
                creator_id="pol_001",
                creator_name="Inspector K. Patil",
                creator_role="police",
                name="City Police Safety Bulletins",
                description="Official live safety updates, verified transit advisories, and active helpline bulletins.",
                category="POLICE_BULLETIN",
                avatar="🚔",
                subscriber_count=320
            )
            ch2 = BroadcastChannel(
                id="chan_002",
                creator_id="prs_001",
                creator_name="Rhea Nair",
                creator_role="journalist",
                name="Press Desk: Urban Transit Audits",
                description="Real-time investigative dispatches on city streetlighting, CCTV coverage, and night safety.",
                category="INVESTIGATIVE_PRESS",
                avatar="📰",
                subscriber_count=180
            )
            db.add_all([ch1, ch2])
            db.flush()

            # Seed channel posts
            cp1 = ChannelPost(
                id="cp_001",
                channel_id="chan_001",
                author_name="Inspector K. Patil",
                title="Emergency Helpline & Quick Response PCR Numbers Active",
                content="Dial 112 or activate the Perimeter SOS button for immediate 5km geofence auto-dispatch. All patrol vehicles are equipped with GPS beacons."
            )
            cp2 = ChannelPost(
                id="cp_002",
                channel_id="chan_002",
                author_name="Rhea Nair",
                title="Bandra-Kurla Transit Corridor Safety Report Published",
                content="Our audit of 45 bus stops across BKC shows 92% compliance with high-mast lighting standards. Full report available on Deccan Herald."
            )
            db.add_all([cp1, cp2])

        # 7. Seed initial SOS incident and Case
        if db.query(SOSIncident).count() == 0:
            inc = SOSIncident(
                incident_id="SOS-2026-9081",
                user_id="usr_001",
                user_name="Aarohi Sharma",
                phone="+91 98200 12345",
                trigger_type="SHAKE_MOTION",
                status="ACTIVE_DISPATCH",
                latitude=19.0760,
                longitude=72.8777,
                accuracy_meters=8.5,
                address="SV Road, Near Metro Pillar #42, Bandra West",
                geofence_radius_km=5.0,
                case_id="CAS-2026-8801"
            )
            db.add(inc)

            res1 = Responder(
                incident_id="SOS-2026-9081",
                responder_id="vol_001",
                responder_name="Priya Deshmukh (Volunteer)",
                role="volunteer",
                eta_minutes=3.2,
                distance_km=1.1,
                status="EN_ROUTE"
            )
            res2 = Responder(
                incident_id="SOS-2026-9081",
                responder_id="pol_001",
                responder_name="Patrol Unit #04 (Police)",
                role="police",
                eta_minutes=5.0,
                distance_km=2.4,
                status="EN_ROUTE"
            )
            db.add_all([res1, res2])

        if db.query(IncidentCase).count() == 0:
            c = IncidentCase(
                case_id="CAS-2026-8801",
                user_id="usr_001",
                title="Emergency Dispatch & Patrol Response",
                victim_identifier="Citizen Aarohi Sharma",
                status="ACTIVE_INVESTIGATION",
                priority="HIGH",
                location="Bandra West Metro Corridor",
                assigned_precinct="Central Police Precinct #01"
            )
            db.add(c)

            t1 = TimelineEvent(
                case_id="CAS-2026-8801",
                title="Motion Shake SOS Triggered",
                description="Accelerometer threshold detected 3x shake sequence ($g > 2.8g$).",
                actor_role="citizen",
                actor_name="Aarohi Sharma"
            )
            t2 = TimelineEvent(
                case_id="CAS-2026-8801",
                title="5 km Geofence Dispatch Sent",
                description="FCM high-priority dispatch routed to 12 nearby volunteers and Patrol Unit #04.",
                actor_role="police",
                actor_name="Command Automation"
            )
            db.add_all([t1, t2])

            a1 = LinkedPressArticle(
                case_id="CAS-2026-8801",
                article_id="art_001",
                title="Rapid Dispatch Tested in Bandra Metro Zone",
                outlet="The Deccan Herald",
                journalist_name="Rhea Nair"
            )
            db.add(a1)

        db.commit()
    finally:
        db.close()

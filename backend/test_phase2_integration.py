"""
PERIMETER Platform - Phase 2 Comprehensive Integration Test Suite
Validates all 5 roles, Universal Social features, Device Media Uploads,
Admin Governance, Real GPS SOS Lifecycle, Heatmap Data, and Route Risk Analysis.
"""
import sys
import os
import io
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User

client = TestClient(app)
db = SessionLocal()
API = "/api/v1"

def run_tests():
    print("=" * 70)
    print("🚀 RUNNING PERIMETER PHASE 2 COMPREHENSIVE INTEGRATION SUITE")
    print("=" * 70)

    # 1. Test Users for all 5 roles
    roles = ["user", "volunteer", "police", "journalist", "admin"]
    user_tokens = {}

    for r in roles:
        u = db.query(User).filter(User.role == r, User.is_active == True).first()
        if not u:
            print(f"❌ Missing active test user for role '{r}' in DB!")
            return False
        token = create_access_token({"sub": u.id, "email": u.email, "role": u.role})
        user_tokens[r] = (u, token)
        print(f"✅ Verified User for Role [{r.upper()}]: {u.name} ({u.email})")

    # 2. Universal Profile for all 5 roles
    print("\n--- 1. Testing Universal Profile Endpoint across all 5 roles ---")
    for r, (u, token) in user_tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get(f"{API}/social/profile/me", headers=headers)
        assert res.status_code == 200, f"Failed {API}/social/profile/me for {r}: {res.text}"
        data = res.json()
        assert data["role"] == r, f"Role mismatch in profile: expected {r}, got {data['role']}"
        assert data["id"] == u.id
        print(f"  ✓ Profile retrieved for {r.upper()}: {data['name']} (@{data['username']}) - Badge: {data['badge_title']}")

    # 3. Post Creation & Universal Social Feed across roles
    print("\n--- 2. Testing Post Creation & Feed across roles ---")
    for r, (u, token) in user_tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        post_payload = {
            "author_name": u.name,
            "author_role": u.role,
            "author_id": u.id,
            "title": f"Test Safety Dispatch from {u.name}",
            "content": f"Live community update testing universal social system for {r}.",
            "tag": "COMMUNITY_UPDATE",
            "location_name": "Marine Drive Safe Sector",
            "media_url": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800",
            "media_type": "image",
            "media_urls": json.dumps(["https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800"])
        }
        res = client.post(f"{API}/feed/", json=post_payload, headers=headers)
        assert res.status_code == 200, f"Failed post creation for {r}: {res.text}"
        post = res.json()
        assert post["author_role"] == r
        print(f"  ✓ Post created by {r.upper()} [{post['id']}]: '{post['title']}'")

    feed_res = client.get(f"{API}/feed/?category=ALL")
    assert feed_res.status_code == 200
    feed_items = feed_res.json()
    assert len(feed_items) >= 5
    print(f"  ✓ Universal Feed contains {len(feed_items)} active community posts across roles.")

    # 4. Device Media Upload Validation & Multipart Storage
    print("\n--- 3. Testing Device Media Uploads & Security Validation ---")
    admin_u, admin_token = user_tokens["admin"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}

    # Test valid image upload
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    files = {"file": ("device_photo.png", fake_png, "image/png")}
    upload_res = client.post(f"{API}/media/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 200, f"Upload single failed: {upload_res.text}"
    upload_data = upload_res.json()
    assert "/uploads/" in upload_data["url"]
    assert upload_data["media_type"] == "image"
    print(f"  ✓ Valid device image uploaded: {upload_data['url']} ({upload_data['size_bytes']} bytes)")

    # Test multiple file upload (up to 10 items)
    multi_files = [
        ("files", ("image_1.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00", "image/jpeg")),
        ("files", ("image_2.png", fake_png, "image/png"))
    ]
    multi_res = client.post(f"{API}/media/upload-multiple", files=multi_files, headers=auth_headers)
    assert multi_res.status_code == 200, f"Upload multiple failed: {multi_res.text}"
    multi_data = multi_res.json()
    assert len(multi_data["urls"]) == 2
    print(f"  ✓ Multi-item device upload successful: {len(multi_data['urls'])} files saved.")

    # Test rejected malicious / executable file
    exe_file = {"file": ("malicious_payload.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-dosexec")}
    bad_res = client.post(f"{API}/media/upload", files=exe_file, headers=auth_headers)
    assert bad_res.status_code == 400, "Security validation failed to block .exe upload!"
    print(f"  ✓ Security validation blocked forbidden file type (.exe) with 400 Bad Request.")

    # 5. Stories, Messages & Channels for All Roles
    print("\n--- 4. Testing Stories, Messages & Broadcast Channels ---")
    for r, (u, token) in user_tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        # Story creation
        story_payload = {
            "author_name": u.name,
            "author_role": u.role,
            "author_id": u.id,
            "caption": f"24H safety patrol status by {u.name}",
            "tag": "PATROL_ACTIVE",
            "media_type": "gradient"
        }
        s_res = client.post(f"{API}/feed/stories", json=story_payload, headers=headers)
        assert s_res.status_code == 200
        print(f"  ✓ 24H Story published by {r.upper()} [{s_res.json()['id']}]")

    channels_res = client.get(f"{API}/social/channels", headers=auth_headers)
    assert channels_res.status_code == 200
    print(f"  ✓ Retrieved {len(channels_res.json())} Broadcast Channels.")

    # 6. Admin Governance & Statistics Suite
    admin_overview_res = client.get(f"{API}/admin/overview", headers=auth_headers)
    assert admin_overview_res.status_code == 200, f"Admin overview failed: {admin_overview_res.text}"
    overview = admin_overview_res.json()
    assert "users" in overview and "incidents" in overview
    print(f"  ✓ Admin Overview KPI: Users: {overview['users']['total']}, Active SOS: {overview['incidents']['active_sos']}, Police: {overview['responders']['police_units']}")

    users_mgmt_res = client.get(f"{API}/admin/users", headers=auth_headers)
    assert users_mgmt_res.status_code == 200
    user_list = users_mgmt_res.json()
    assert len(user_list) >= 5
    # Verify password hashes are strictly absent
    for user_entry in user_list:
        assert "hashed_password" not in user_entry and "password" not in user_entry
    print(f"  ✓ Admin User Directory: {len(user_list)} accounts loaded (passwords strictly omitted).")

    # Content moderation endpoint
    posts_mod_res = client.get(f"{API}/admin/content/posts", headers=auth_headers)
    assert posts_mod_res.status_code == 200
    print(f"  ✓ Admin Content Moderation: {len(posts_mod_res.json())} posts audited.")

    # 7. Real GPS SOS Lifecycle with Continuous Live Location Updates
    print("\n--- 6. Testing Real GPS Emergency SOS Lifecycle ---")
    citizen_u, citizen_token = user_tokens["user"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # Step A: Trigger SOS with genuine GPS coordinates
    sos_trigger_payload = {
        "user_name": citizen_u.name,
        "user_id": citizen_u.id,
        "phone": citizen_u.phone or "+919876543210",
        "trigger_type": "MANUAL_HOLD",
        "severity": "CRITICAL",
        "location": {
            "latitude": 19.0760,
            "longitude": 72.8777,
            "accuracy_meters": 4.5,
            "address": "Linking Road, Bandra West, Mumbai"
        },
        "notes": "Automated Phase 2 Integration Test Emergency SOS."
    }
    sos_res = client.post(f"{API}/sos/trigger", json=sos_trigger_payload, headers=citizen_headers)
    assert sos_res.status_code == 200, f"SOS trigger failed: {sos_res.text}"
    sos_data = sos_res.json()
    inc_id = sos_data["incident_id"]
    print(f"  ✓ SOS Distress beacon broadcasted: ID {inc_id} (Case: {sos_data['case_id']})")

    # Step B: Check Active SOS list for Police & Volunteers
    police_u, police_token = user_tokens["police"]
    police_headers = {"Authorization": f"Bearer {police_token}"}
    active_sos_res = client.get(f"{API}/sos/active", headers=police_headers)
    assert active_sos_res.status_code == 200
    active_items = active_sos_res.json()
    found_sos = [i for i in active_items if i["incident_id"] == inc_id]
    assert len(found_sos) == 1
    print(f"  ✓ Police active SOS queue: Emergency {inc_id} visible with full coordinates ({found_sos[0]['location']['latitude']}, {found_sos[0]['location']['longitude']})")

    # Step C: Continuous Live Location Update (Moving Victim GPS)
    live_loc_payload = {
        "latitude": 19.0765,
        "longitude": 72.8782,
        "accuracy_meters": 3.8,
        "address": "Moving north along Linking Road"
    }
    loc_up_res = client.post(f"{API}/sos/{inc_id}/location", json=live_loc_payload, headers=citizen_headers)
    assert loc_up_res.status_code == 200, f"Live location update failed: {loc_up_res.text}"
    print(f"  ✓ Live Location Update streamed for {inc_id}: Coordinates updated to (19.0765, 72.8782)")

    # Step D: Police Acknowledgement & Dispatch
    ack_res = client.post(f"{API}/sos/{inc_id}/acknowledge", headers=police_headers)
    assert ack_res.status_code == 200
    print(f"  ✓ Police Command acknowledged dispatch {inc_id}.")

    # Step E: Resolve SOS
    resolve_res = client.post(f"{API}/sos/{inc_id}/resolve?resolved_by=Inspector%20Patil&notes=Phase%202%20Integration%20Test%20Complete", headers=police_headers)
    assert resolve_res.status_code == 200
    print(f"  ✓ SOS {inc_id} successfully marked as RESOLVED. Timeline closed.")

    # 8. Safe Route Risk Analysis & Comparison
    print("\n--- 7. Testing Safe Route Corridor Risk Analysis ---")
    route_res = client.get(f"{API}/safe-routes/?from_lat=19.0596&from_lng=72.8295&to_lat=19.1136&to_lng=72.8697", headers=citizen_headers)
    assert route_res.status_code == 200, f"Route analysis failed: {route_res.text}"
    route_data = route_res.json()
    assert "routes" in route_data and len(route_data["routes"]) >= 2
    fastest = route_data["routes"][0]
    safer = route_data["routes"][1]
    print(f"  ✓ Route Analysis: Evaluated {len(route_data['routes'])} routes.")
    print(f"    - Route 1: {fastest['name']} (Risk Score: {fastest['safety_risk_score']}/100, Dist: {fastest['distance_km']}km)")
    print(f"    - Route 2: {safer['name']} (Risk Score: {safer['safety_risk_score']}/100, Dist: {safer['distance_km']}km)")

    # 9. Heatmap Data & Crime Attribution
    print("\n--- 8. Testing Geospatial Heatmap & Data Sources ---")
    heatmap_res = client.get(f"{API}/heatmap?city=Mumbai")
    assert heatmap_res.status_code == 200, f"Heatmap failed: {heatmap_res.text}"
    heatmap_data = heatmap_res.json()
    assert "areas" in heatmap_data and len(heatmap_data["areas"]) > 0
    print(f"  ✓ Heatmap retrieved {len(heatmap_data['areas'])} sector risk polygons and {len(heatmap_data.get('incidents', []))} active incident markers.")
    print(f"  ✓ Attribution data sources: {heatmap_data['areas'][0]['data_sources']}")

    print("\n" + "=" * 70)
    print("🏆 ALL PHASE 2 INTEGRATION TESTS PASSED (100% SUCCESS)")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

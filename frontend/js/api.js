/**
 * PERIMETER Platform — Unified Frontend API & Persistent Auth Client
 * Full Social Community & Women Safety Emergency Dispatch Support
 */

const API_BASE = 'http://127.0.0.1:8000/api/v1';
const SESSION_KEY = 'perimeter_session';
const TOKEN_KEY = 'perimeter_jwt_token';

const ROLE_DASHBOARDS = {
    'user': 'user.html',
    'volunteer': 'volunteer.html',
    'police': 'police.html',
    'journalist': 'journalist.html',
    'admin': 'admin.html'
};

const ROLE_BADGE_TITLES = {
    'user': 'Citizen User',
    'volunteer': 'Verified Responder',
    'police': 'City Police Command',
    'journalist': 'Press Reporter',
    'admin': 'Super Administrator'
};

/**
 * Retrieve saved JWT token
 */
function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Retrieve saved user session
 */
function getCurrentUser() {
    try {
        const raw = localStorage.getItem(SESSION_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        console.error('Error parsing session data', e);
        return null;
    }
}

/**
 * Save persistent user session
 */
function saveSession(token, user) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    if (user) {
        localStorage.setItem(SESSION_KEY, JSON.stringify(user));
        // Keep legacy keys synced for seamless interoperability
        if (user.role === 'user') {
            localStorage.setItem('perimeter_user_profile', JSON.stringify({
                username: user.name,
                email: user.email,
                phone: user.phone,
                emergencyContact: user.dynamic_field_1,
                area: user.dynamic_field_2,
                registeredAt: new Date().toISOString()
            }));
        } else if (user.role === 'volunteer') {
            localStorage.setItem('perimeter_vol_profile', JSON.stringify({
                name: user.name,
                volId: user.dynamic_field_1,
                area: user.dynamic_field_2,
                registeredAt: new Date().toISOString()
            }));
        } else if (user.role === 'police') {
            localStorage.setItem('perimeter_police_profile', JSON.stringify({
                name: user.name,
                badge: user.dynamic_field_1,
                precinct: user.dynamic_field_2,
                registeredAt: new Date().toISOString()
            }));
        } else if (user.role === 'journalist') {
            localStorage.setItem('perimeter_press_profile', JSON.stringify({
                name: user.name,
                pressId: user.dynamic_field_1,
                outlet: user.dynamic_field_2,
                registeredAt: new Date().toISOString()
            }));
        }
    }
}window.saveSession = saveSession;

/**
 * Clear session and logout
 */
function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem('perimeter_user_profile');
    localStorage.removeItem('perimeter_vol_profile');
    localStorage.removeItem('perimeter_police_profile');
    localStorage.removeItem('perimeter_press_profile');
    window.location.href = 'register.html';
}

/**
 * Generic API Fetch helper
 */
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {};

    if (body && !(body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const token = getAuthToken();

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers: headers
    };

    if (body) {
        options.body = body instanceof FormData
            ? body
            : JSON.stringify(body);
    }

    const url = endpoint.startsWith('http')
        ? endpoint
        : `${API_BASE}${endpoint}`;

    try {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => null);

        if (response.status === 401) {
            console.warn('PERIMETER API authentication failed.');

            const errorMsg =
                data?.detail ||
                'Your session is no longer valid. Please log in again.';

            throw new Error(errorMsg);
        }

        if (!response.ok) {
            const errorMsg =
                data?.detail ||
                `API request failed with status ${response.status}`;

            throw new Error(errorMsg);
        }

        return data;

    } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            console.error(`[PERIMETER Server Connection Error] Could not connect to API server at ${API_BASE}. Make sure the FastAPI backend is running on port 8000.`);
            showToast('⚠️ Backend server (port 8000) not reachable. Please run: npm run backend', '🔌', 5000);
            throw new Error(`Cannot connect to PERIMETER backend at ${API_BASE}. Please ensure port 8000 server is active.`);
        }
        console.warn(`[PERIMETER API Error] ${method} ${endpoint}:`, err.message);
        throw err;
    }
}
    window.apiCall = apiCall;
/**
 * Page Auth Guard for Public Pages (register.html):
 * If user is already authenticated, automatically forwards to their role dashboard.
 */
function guardPublicPage() {
    const user = getCurrentUser();
    const token = getAuthToken();
    if (user && token && user.role && ROLE_DASHBOARDS[user.role]) {
        console.log(`[Auth Guard] Active session detected for ${user.name} (${user.role}). Auto-routing to dashboard...`);
        window.location.replace(ROLE_DASHBOARDS[user.role]);
        return true;
    }
    return false;
}

/**
 * Page Auth Guard for Protected Dashboards:
 * Checks if user is authenticated and authorized for the page.
 */
async function guardProtectedPage(allowedRoles = []) {
    const user = getCurrentUser();
    const token = getAuthToken();

    if (!user || !token) {
        console.warn('[Auth Guard] No active session found. Redirecting to registration...');
        window.location.replace('register.html');
        return null;
    }

    // Role check (Admin has universal access)
    if (allowedRoles.length > 0 && user.role !== 'admin' && !allowedRoles.includes(user.role)) {
        console.warn(`[Auth Guard] Role '${user.role}' not permitted for this dashboard. Redirecting to assigned dashboard...`);
        const target = ROLE_DASHBOARDS[user.role] || 'user.html';
        window.location.replace(target);
        return null;
    }

    // Background verify token
    try {
        apiCall('/auth/me').catch(err => {
            console.warn('[Auth Guard] Background token verify notice:', err.message);
        });
    } catch(e) {}

    return user;
}

/**
/*Unified Toast Notification*/

let toastTimer = null;

function showToast(msg, icon = '✨', duration = 3200) {
    let el = document.getElementById('toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'toast';
        el.className = 'toast';
        el.style.cssText = `
            position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(100px);
            background: #1E293B; color: #FFF; border: 1px solid #334155; padding: 12px 24px;
            border-radius: 40px; display: flex; align-items: center; gap: 10px; font-size: 14px;
            font-weight: 500; box-shadow: 0 10px 30px rgba(0,0,0,0.5); opacity: 0;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); z-index: 99999;
        `;
        el.innerHTML = `<span id="toastIcon">${icon}</span><span id="toastMsg">${msg}</span>`;
        document.body.appendChild(el);
    } else {
        const iconEl = document.getElementById('toastIcon');
        const msgEl = document.getElementById('toastMsg');
        if (iconEl) iconEl.textContent = icon;
        if (msgEl) msgEl.textContent = msg;
    }

    el.style.opacity = '1';
    el.style.transform = 'translateX(-50%) translateY(0)';

    setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateX(-50%) translateY(100px)';
    }, duration);
}

/*Global alias for compatibility*/
window.showToast = showToast;
const toast = showToast;

/* -------------------------------------------------------------
   SOCIAL API METHODS
------------------------------------------------------------- */

const SocialAPI = {
    // Profile
    async getMyProfile() {
        return await apiCall('/social/profile/me');
    },
    async updateMyProfile(data) {
        return await apiCall('/social/profile/me', 'PUT', data);
    },
    async getUserProfile(userId) {
        return await apiCall(`/social/users/${userId}/profile`);
    },
    async searchUsers(query = '', role = '') {
        const params = [];
        if (query && query.trim()) params.push(`q=${encodeURIComponent(query.trim())}`);
        if (role && role.trim() && role.trim().toLowerCase() !== 'all') params.push(`role=${encodeURIComponent(role.trim().toLowerCase())}`);
        const qs = params.length > 0 ? `?${params.join('&')}` : '';
        return await apiCall(`/social/users/search${qs}`);
    },
    async getAllUsers(role = '') {
        const qs = role && role.trim() && role.trim().toLowerCase() !== 'all' ? `?role=${encodeURIComponent(role.trim().toLowerCase())}` : '';
        return await apiCall(`/auth/users${qs}`);
    },

    // Follows
    async followUser(userId) {
        return await apiCall(`/social/users/${userId}/follow`, 'POST');
    },
    async unfollowUser(userId) {
        return await apiCall(`/social/users/${userId}/unfollow`, 'POST');
    },
    async getFollowers(userId) {
        return await apiCall(`/social/users/${userId}/followers`);
    },
    async getFollowing(userId) {
        return await apiCall(`/social/users/${userId}/following`);
    },
    async getFollowRequests() {
        return await apiCall('/social/follow-requests');
    },
    async respondFollowRequest(requestId, action) {
        return await apiCall(`/social/follow-requests/${requestId}/respond?action=${action}`, 'POST');
    },

    // Feed & Posts
    async getFeed(category = 'ALL') {
        return await apiCall(`/feed/?category=${category}`);
    },
    async createPost(postData) {
        return await apiCall('/feed/', 'POST', postData);
    },
    async toggleLike(postId) {
        return await apiCall(`/social/posts/${postId}/like`, 'POST');
    },
    async getComments(postId) {
        return await apiCall(`/social/posts/${postId}/comments`);
    },
    async addComment(postId, text) {
        return await apiCall(`/social/posts/${postId}/comments`, 'POST', { text });
    },
    async deleteComment(commentId) {
        return await apiCall(`/social/comments/${commentId}`, 'DELETE');
    },
    async sharePost(postId, target = 'community_network') {
        return await apiCall(`/social/posts/${postId}/share`, 'POST', { target });
    },
    async toggleSave(postId) {
        return await apiCall(`/social/posts/${postId}/save`, 'POST');
    },

    // Stories
    async getStories() {
        return await apiCall('/feed/stories');
    },
    async createStory(storyData) {
        return await apiCall('/feed/stories', 'POST', storyData);
    },
    async voteStoryPoll(storyId, option) {
        return await apiCall(`/social/stories/${storyId}/vote`, 'POST', { option });
    },

    // Reels
    async getReels() {
        return await apiCall('/social/reels');
    },
    async createReel(reelData) {
        return await apiCall('/social/reels', 'POST', reelData);
    },
    async toggleReelLike(reelId) {
        return await apiCall(`/social/reels/${reelId}/like`, 'POST');
    },

    // Direct Messages
    async getConversations() {
        return await apiCall('/social/conversations');
    },
    async startConversation(recipientId) {
        return await apiCall('/social/conversations', 'POST', { recipient_id: recipientId });
    },
    async getMessages(convId) {
        return await apiCall(`/social/conversations/${convId}/messages`);
    },
    async sendMessage(convId, text, mediaUrl = null) {
        return await apiCall(`/social/conversations/${convId}/messages`, 'POST', { text, media_url: mediaUrl });
    },

    // Broadcast Channels
    async getChannels() {
        return await apiCall('/social/channels');
    },
    async createChannel(channelData) {
        return await apiCall('/social/channels', 'POST', channelData);
    },
    async toggleSubscribeChannel(channelId) {
        return await apiCall(`/social/channels/${channelId}/subscribe`, 'POST');
    },
    async getChannelPosts(channelId) {
        return await apiCall(`/social/channels/${channelId}/posts`);
    },
    async publishChannelPost(channelId, postData) {
        return await apiCall(`/social/channels/${channelId}/posts`, 'POST', postData);
    },

    // Profile Activity Lists
    async getMyPosts() {
        return await apiCall('/social/profile/my-posts');
    },
    async getMyLikedPosts() {
        return await apiCall('/social/profile/my-liked-posts');
    },
    async getMySavedPosts() {
        return await apiCall('/social/profile/my-saved-posts');
    },
    async getMyCases() {
        return await apiCall('/social/profile/my-cases');
    },

        // SOS Emergency Dispatch
        async triggerSOS(sosData) {
            return await apiCall('/sos/trigger', 'POST', sosData);
        },
    
        async getActiveSOS() {
            return await apiCall('/sos/active');
        },

        async getSOS(incidentId) {
            return await apiCall(`/sos/${encodeURIComponent(incidentId)}`);
        },

        async acknowledgeSOS(incidentId) {
            return await apiCall(`/sos/${encodeURIComponent(incidentId)}/acknowledge`, 'POST');
        },

        async dispatchSOS(incidentId, responderId, responderName, role = 'police') {
            const params = new URLSearchParams({
                responder_id: responderId,
                responder_name: responderName,
                role: role
            });
            return await apiCall(`/sos/${encodeURIComponent(incidentId)}/dispatch?${params.toString()}`, 'POST');
        },
    
        async respondToSOS(incidentId, responderId, responderName, role) {
            const params = new URLSearchParams({
                responder_id: responderId,
                responder_name: responderName,
                role: role
            });
    
            return await apiCall(
                `/sos/${encodeURIComponent(incidentId)}/respond?${params.toString()}`,
                'POST'
            );
        },
    
        async resolveSOS(incidentId, resolvedBy, notes = null) {
            const params = new URLSearchParams({
                resolved_by: resolvedBy
            });
    
            if (notes) {
                params.append('notes', notes);
            }
    
            return await apiCall(
                `/sos/${encodeURIComponent(incidentId)}/resolve?${params.toString()}`,
                'POST'
            );
        },

        async updateSOSLocation(incidentId, locationData) {
            return await apiCall(
                `/sos/${encodeURIComponent(incidentId)}/location`,
                'POST',
                locationData
            );
        }
    };
    window.SocialAPI = SocialAPI;
    window.SOSAPI = SocialAPI; // Alias

/* -------------------------------------------------------------
   LOCATION & GEOFENCE API
------------------------------------------------------------- */
const LocationAPI = {
    async updateLocation(data) {
        return await apiCall('/location/update', 'POST', data);
    },
    async getMyLocation() {
        return await apiCall('/location/me');
    },
    async getResponders() {
        return await apiCall('/location/responders');
    },
    async getNearbyVolunteers(lat, lng, radiusKm = 5.0) {
        return await apiCall(`/location/nearby-volunteers?lat=${lat}&lng=${lng}&radius_km=${radiusKm}`);
    }
};
window.LocationAPI = LocationAPI;

/* -------------------------------------------------------------
   HEATMAP & SAFE ROUTING API
------------------------------------------------------------- */
const SafetyMapAPI = {
    async getHeatmap(city = 'Mumbai') {
        return await apiCall(`/heatmap?city=${encodeURIComponent(city)}`);
    },
    async getSafetyScore(lat, lng) {
        return await apiCall(`/safety-score?lat=${lat}&lng=${lng}`);
    },
    async getSafeRoutes(fromLat, fromLng, toLat, toLng) {
        return await apiCall(`/safe-routes/?from_lat=${fromLat}&from_lng=${fromLng}&to_lat=${toLat}&to_lng=${toLng}`);
    }
};
window.SafetyMapAPI = SafetyMapAPI;

/* -------------------------------------------------------------
   NOTIFICATIONS API & REAL-TIME WEBSOCKET
------------------------------------------------------------- */
const NotificationAPI = {
    async getNotifications(limit = 20) {
        return await apiCall(`/notifications/?limit=${limit}`);
    },
    async markRead(notificationId) {
        return await apiCall(`/notifications/${notificationId}/read`, 'POST');
    },
    connectWebSocket(role, onMessageCallback) {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = '127.0.0.1:8000';
            const ws = new WebSocket(`${protocol}//${host}/api/v1/notifications/ws/${role}`);
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (onMessageCallback) onMessageCallback(data);
                } catch(e) {}
            };
            ws.onerror = (e) => {
                console.warn('[WS Alert Error] Fallback polling active.', e);
            };
            return ws;
        } catch (e) {
            console.warn('[WS Alert Exception]', e);
            return null;
        }
    }
};
window.NotificationAPI = NotificationAPI;

/* -------------------------------------------------------------
   ADMIN GOVERNANCE & DATABASE AUDIT API
------------------------------------------------------------- */
const AdminAPI = {
    async getUsers(role = '') {
        const qs = role && role !== 'all' ? `?role=${encodeURIComponent(role)}` : '';
        return await apiCall(`/admin/users${qs}`);
    },
    async getDetailedStats() {
        return await apiCall('/admin/statistics');
    },
    async getIncidents(status = '') {
        const qs = status && status !== 'all' ? `?status_filter=${encodeURIComponent(status)}` : '';
        return await apiCall(`/admin/incidents${qs}`);
    },
    async getSOSEvents() {
        return await apiCall('/admin/sos');
    },
    async getLocations() {
        return await apiCall('/admin/locations');
    },
    async deleteUser(userId) {
        return await apiCall(`/admin/users/${userId}`, 'DELETE');
    },
    async toggleUserStatus(userId, isActive) {
        return await apiCall(`/admin/users/${userId}/status`, 'PUT', { is_active: isActive });
    },
    async updateUserRole(userId, role) {
        return await apiCall(`/admin/users/${userId}/role`, 'PUT', { role });
    },
    async getContentPosts() {
        return await apiCall('/admin/content/posts');
    },
    async deleteContentPost(postId) {
        return await apiCall(`/admin/content/posts/${postId}`, 'DELETE');
    }
};
window.AdminAPI = AdminAPI;

/* -------------------------------------------------------------
   DEVICE MEDIA UPLOAD API (Camera / Gallery / File Picker)
------------------------------------------------------------- */
const MediaAPI = {
    async uploadSingle(file) {
        const formData = new FormData();
        formData.append('file', file);
        const token = getAuthToken();
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE_URL}/media/upload`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to upload media file.');
        }
        return await res.json();
    },

    async uploadMultiple(files) {
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        const token = getAuthToken();
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE_URL}/media/upload-multiple`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to upload media files.');
        }
        return await res.json();
    }
};
window.MediaAPI = MediaAPI;


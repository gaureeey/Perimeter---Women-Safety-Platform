/**
 * PERIMETER Platform — Real Geolocation & Privacy-Preserving Location Service
 * Clean abstraction over browser Geolocation API with purpose-based consent.
 */

const LocationService = {
    watchId: null,
    lastKnownPosition: null,
    isTrackingEmergency: false,
    
    // Default fallback center (Mumbai Central Safety Sector) if GPS is denied in demo/offline
    DEFAULT_CENTER: {
        latitude: 19.0596,
        longitude: 72.8295,
        accuracy: 15.0,
        isFallback: true,
        address: "Bandra West, Mumbai (Default Demo Zone)"
    },

    /**
     * Check if geolocation is supported by the browser environment
     */
    isSupported() {
        return 'geolocation' in navigator;
    },

    /**
     * Query current permission status
     */
    async queryPermission() {
        if (!navigator.permissions || !navigator.permissions.query) {
            return 'unknown';
        }
        try {
            const status = await navigator.permissions.query({ name: 'geolocation' });
            return status.state; // 'granted', 'prompt', 'denied'
        } catch (e) {
            return 'unknown';
        }
    },

    /**
     * Request one-time high accuracy position (for SOS or User Intent)
     */
    async getCurrentPosition(highAccuracy = true) {
        if (!this.isSupported()) {
            console.warn('[LocationService] Geolocation not supported. Using fallback position.');
            return this.DEFAULT_CENTER;
        }

        return new Promise((resolve) => {
            const options = {
                enableHighAccuracy: highAccuracy,
                timeout: 8000,
                maximumAge: 10000
            };

            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const result = {
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        timestamp: new Date(pos.timestamp).toISOString(),
                        isFallback: false,
                        address: `GPS Lat ${pos.coords.latitude.toFixed(4)}, Lng ${pos.coords.longitude.toFixed(4)}`
                    };
                    this.lastKnownPosition = result;
                    resolve(result);
                },
                (err) => {
                    console.warn(`[LocationService] GPS error (${err.code}): ${err.message}. Using safe fallback.`);
                    let userMsg = "Using default regional map center.";
                    if (err.code === err.PERMISSION_DENIED) {
                        userMsg = "Location permission denied. Using safe sector coordinates.";
                    } else if (err.code === err.POSITION_UNAVAILABLE) {
                        userMsg = "GPS signal unavailable. Using last known sector.";
                    }
                    if (window.showToast) window.showToast(userMsg, '📍');

                    resolve(this.lastKnownPosition || this.DEFAULT_CENTER);
                },
                options
            );
        });
    },

    /**
     * Controlled emergency tracking for active SOS
     * Only updates while emergency is active
     */
    startEmergencyTracking(onUpdateCallback) {
        if (!this.isSupported() || this.watchId !== null) return;

        this.isTrackingEmergency = true;
        console.log('[LocationService] Active Emergency tracking initiated.');

        this.watchId = navigator.geolocation.watchPosition(
            async (pos) => {
                const current = {
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    accuracy: pos.coords.accuracy,
                    timestamp: new Date(pos.timestamp).toISOString(),
                    isFallback: false
                };
                this.lastKnownPosition = current;

                // Sync with backend under EMERGENCY privacy level
                if (window.apiCall) {
                    try {
                        await window.apiCall('/location/update', 'POST', {
                            latitude: current.latitude,
                            longitude: current.longitude,
                            accuracy: current.accuracy,
                            source: 'browser_gps',
                            privacy_level: 'EMERGENCY'
                        });
                    } catch (e) {
                        console.warn('[LocationService] Failed to sync emergency location update:', e.message);
                    }
                }

                if (typeof onUpdateCallback === 'function') {
                    onUpdateCallback(current);
                }
            },
            (err) => {
                console.warn('[LocationService] Emergency watch error:', err.message);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 5000
            }
        );
    },

    /**
     * Stop emergency location updates
     */
    stopEmergencyTracking() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
        this.isTrackingEmergency = false;
        console.log('[LocationService] Emergency tracking stopped.');
    },

    /**
     * Explicitly send user location to backend (e.g. when checking safety map)
     */
    async syncCurrentLocation(privacyLevel = 'EMERGENCY') {
        const pos = await this.getCurrentPosition();
        if (window.apiCall && !pos.isFallback) {
            try {
                return await window.apiCall('/location/update', 'POST', {
                    latitude: pos.latitude,
                    longitude: pos.longitude,
                    accuracy: pos.accuracy,
                    source: 'browser_gps',
                    privacy_level: privacyLevel
                });
            } catch (e) {
                console.warn('[LocationService] Sync notice:', e.message);
            }
        }
        return pos;
    }
};

window.LocationService = LocationService;

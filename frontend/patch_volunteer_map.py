#!/usr/bin/env python3
"""Usage:  python patch_volunteer_map.py [path/to/volunteer.html]
Backs up the file to volunteer.html.bak, then swaps the fake canvas radar +
canvas HUD route for real interactive maps (Leaflet + CARTO/OSM tiles, no API key)."""
import re, shutil, sys

path = sys.argv[1] if len(sys.argv) > 1 else "volunteer.html"
s = open(path, encoding="utf-8").read()
shutil.copy(path, path + ".bak")

CSS = r"""
        /* ── REAL MAP (Leaflet) ── */
        .radar-canvas-box { position: relative; }
        #liveMap, #hudMap { width: 100%; z-index: 0; isolation: isolate; background: #E5E3DF; }
        #liveMap { height: 380px; }
        #hudMap { height: 230px; }
        .leaflet-container { font-family: var(--sans); }
        .map-recenter {
            position: absolute; left: 10px; bottom: 28px; z-index: 500;
            background: #fff; color: #111827; border: none; border-radius: 8px;
            padding: 8px 12px; font-size: 12px; font-weight: 700; cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,.3);
        }
        .map-recenter:hover { background: #FEF3C7; }
        .map-legend {
            position: absolute; left: 10px; top: 10px; z-index: 500; background: rgba(255,255,255,.95);
            border-radius: 8px; padding: 6px 10px; font-size: 11px; font-weight: 600; color: #111827;
            box-shadow: 0 2px 8px rgba(0,0,0,.25); line-height: 1.6;
        }
        .vol-dot { position: relative; width: 22px; height: 22px; }
        .vol-dot::before { content: ''; position: absolute; inset: 0; border-radius: 50%; background: rgba(37,99,235,.3); animation: mapPulse 2s infinite; }
        .vol-dot span { position: absolute; inset: 4px; border-radius: 50%; background: #2563EB; border: 3px solid #fff; box-shadow: 0 1px 6px rgba(0,0,0,.4); }
        .inc-pin { position: relative; width: 34px; height: 34px; }
        .inc-pin::before { content: ''; position: absolute; inset: 0; border-radius: 50%; background: rgba(255,90,95,.35); animation: mapPulse 1.6s infinite; }
        .inc-pin span { position: absolute; inset: 4px; border-radius: 50%; background: #EF4444; border: 2px solid #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,.4); }
        .inc-pin.med span { background: #F59E0B; }
        .map-pop b { display: block; font-size: 13px; margin-bottom: 2px; }
        .map-pop small { color: #64748B; display: block; margin-bottom: 8px; }
        .map-pop button { background: #D97706; color: #fff; border: none; border-radius: 100px; padding: 6px 12px; font-weight: 700; font-size: 12px; cursor: pointer; }
        @keyframes mapPulse { 0% { transform: scale(.5); opacity: 1; } 100% { transform: scale(1.6); opacity: 0; } }
"""

JS = r"""// ── LIVE MAP (replaces fake canvas radar) ──
        let liveMap = null, volMarker = null, rangeCircle = null, incLayer = null, firstFix = true;
        let volPos = { lat: 12.9716, lng: 77.5946 };
        const incidentsById = {};
        const incCoords = {};

        function makeTiles(kind) {
            if (kind === 'dark') return L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19, subdomains: 'abcd', attribution: '© OpenStreetMap © CARTO' });
            if (kind === 'sat') return L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Tiles © Esri' });
            return L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 19, subdomains: 'abcd', attribution: '© OpenStreetMap © CARTO' });
        }

        function incPos(inc) {
            const l = inc.location || {};
            const lat = l.latitude ?? l.lat ?? inc.latitude ?? inc.lat;
            const lng = l.longitude ?? l.lng ?? l.lon ?? inc.longitude ?? inc.lng;
            if (lat == null || lng == null || isNaN(lat) || isNaN(lng)) return null;
            return [Number(lat), Number(lng)];
        }

        function setVolPos(lat, lng) {
            volPos = { lat, lng };
            if (!liveMap) return;
            volMarker.setLatLng([lat, lng]);
            rangeCircle.setLatLng([lat, lng]);
            const g = document.getElementById('gpsText');
            if (g) g.textContent = `GPS: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`;
            if (firstFix) { firstFix = false; recenterMap(); }
        }

        function recenterMap() {
            if (liveMap && rangeCircle) liveMap.fitBounds(rangeCircle.getBounds(), { padding: [10, 10] });
        }

        function initLiveMap() {
            const el = document.getElementById('liveMap');
            if (!el || liveMap || typeof L === 'undefined') return;
            liveMap = L.map(el, { zoomControl: false }).setView([volPos.lat, volPos.lng], 13);
            const voyager = makeTiles('voyager').addTo(liveMap);
            L.control.layers({ 'Map': voyager, 'Dark': makeTiles('dark'), 'Satellite': makeTiles('sat') }, null, { position: 'topright' }).addTo(liveMap);
            L.control.zoom({ position: 'bottomright' }).addTo(liveMap);
            rangeCircle = L.circle([volPos.lat, volPos.lng], { radius: 5000, color: '#D97706', weight: 2, dashArray: '6 6', fillColor: '#F59E0B', fillOpacity: 0.08 }).addTo(liveMap);
            volMarker = L.marker([volPos.lat, volPos.lng], {
                icon: L.divIcon({ className: '', html: '<div class="vol-dot"><span></span></div>', iconSize: [22, 22], iconAnchor: [11, 11] }),
                zIndexOffset: 1000
            }).addTo(liveMap).bindTooltip('You (Volunteer)');
            incLayer = L.layerGroup().addTo(liveMap);
            recenterMap();
            setTimeout(() => liveMap.invalidateSize(), 300);

            if (navigator.geolocation) {
                navigator.geolocation.watchPosition(
                    p => setVolPos(p.coords.latitude, p.coords.longitude),
                    () => console.warn('Location denied, using default Bengaluru centre'),
                    { enableHighAccuracy: true, maximumAge: 10000 }
                );
            }
        }

        function updateMapIncidents(list) {
            if (!liveMap || !incLayer) return;
            incLayer.clearLayers();
            (list || []).forEach(inc => {
                const id = String(inc.incident_id || inc.id || '');
                incidentsById[id] = inc;
                const pos = incPos(inc);
                if (!pos) return;
                incCoords[id] = pos;
                const sev = String(inc.severity || 'MEDIUM').toUpperCase();
                const hot = sev === 'HIGH' || sev === 'CRITICAL';
                const m = L.marker(pos, {
                    icon: L.divIcon({ className: '', html: `<div class="inc-pin ${hot ? '' : 'med'}"><span>🚨</span></div>`, iconSize: [34, 34], iconAnchor: [17, 17] })
                }).addTo(incLayer);
                m.bindPopup(`<div class="map-pop"><b>${escapeDispatchHtml(inc.user_name || 'Citizen')} · ${escapeDispatchHtml(sev)}</b>
                    <small>${escapeDispatchHtml(inc.location?.address || 'Live GPS location')}</small>
                    <button onclick="acceptFromMap('${escapeDispatchHtml(id)}')">Accept & Route →</button></div>`);
            });
        }

        function acceptFromMap(id) {
            const inc = incidentsById[id];
            if (!inc) return;
            acceptDispatch(id, inc.user_name || 'Citizen', inc.location?.address || 'Live GPS location',
                inc.distance_km != null ? `${Number(inc.distance_km).toFixed(1)} km` : 'within 5 km');
        }"""

HUD_JS = r"""let hudMap = null, hudLayer = null;
        async function drawHudRoute() {
            const el = document.getElementById('hudMap');
            if (!el || typeof L === 'undefined') return;
            if (!hudMap) {
                hudMap = L.map(el, { zoomControl: false });
                makeTiles('voyager').addTo(hudMap);
                hudLayer = L.layerGroup().addTo(hudMap);
            }
            await new Promise(r => setTimeout(r, 150));
            hudMap.invalidateSize();
            hudLayer.clearLayers();

            const from = [volPos.lat, volPos.lng];
            const to = incCoords[currentIncidentId] || [volPos.lat + 0.006, volPos.lng + 0.006];
            let pts = [from, to];
            hudMap.fitBounds(L.latLngBounds(pts), { padding: [40, 40] });

            try {
                const r = await fetch(`https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`);
                const j = await r.json();
                const rt = j.routes && j.routes[0];
                if (rt) {
                    pts = rt.geometry.coordinates.map(c => [c[1], c[0]]);
                    const eta = document.getElementById('hudEta');
                    if (eta) eta.textContent = `${Math.max(1, Math.round(rt.duration / 60))} MIN`;
                }
            } catch (e) { console.warn('Route service unavailable, showing straight line'); }

            L.polyline(pts, { color: '#1D4ED8', weight: 6, opacity: 0.9 }).addTo(hudLayer);
            L.circleMarker(from, { radius: 8, color: '#fff', weight: 3, fillColor: '#2563EB', fillOpacity: 1 }).addTo(hudLayer).bindTooltip('You');
            L.circleMarker(to, { radius: 9, color: '#fff', weight: 3, fillColor: '#EF4444', fillOpacity: 1 }).addTo(hudLayer).bindTooltip(activeDispatchTarget || 'Target');
            hudMap.fitBounds(L.latLngBounds(pts), { padding: [30, 30] });
        }"""

MAP_HTML = """<div id="liveMap"></div>
                    <div class="map-legend">🔵 You &nbsp; 🔴 SOS &nbsp; ◌ 5 km range</div>
                    <button type="button" class="map-recenter" onclick="recenterMap()">◎ Re-center</button>"""

def sub(pattern, repl, flags=re.S, label=""):
    global s
    new, n = re.subn(pattern, lambda m: repl(m) if callable(repl) else repl, s, count=1, flags=flags)
    print(("OK   " if n else "MISS ") + label)
    s = new

sub(r"<style>", lambda m: '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">\n    <style>', label="leaflet css")
sub(r"</style>", lambda m: CSS + "    </style>", label="map css")
sub(r'<canvas id="radarCanvas"[^>]*></canvas>', MAP_HTML, label="radar canvas -> map div")
sub(r'<canvas id="hudCanvas"[^>]*></canvas>', '<div id="hudMap" class="hud-map-canvas"></div>', label="hud canvas -> map div")
sub(r"<span>GPS: 12\.9716° N, 77\.5946° E</span>", '<span id="gpsText">GPS: 12.9716° N, 77.5946° E</span>', label="gps text id")
sub(r'<script src="js/api\.js"></script>', '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>\n    <script src="js/api.js"></script>', label="leaflet js")
sub(r"// Radar Canvas Simulation.*?requestAnimationFrame\(drawRadar\);\s*\}", JS, label="radar fn -> live map")
sub(r"function drawHudRoute\(\) \{.*?fillText\('Target \(0\.8km\)', 350, 30\);\s*\}", HUD_JS, label="hud route fn")
sub(r"drawRadar\(\);", "initLiveMap();", label="init call")
sub(r"updateActiveIncidentCount\(liveIncidents\.length\);(\s*// Remove any previous)",
    lambda m: "updateActiveIncidentCount(liveIncidents.length);\n                updateMapIncidents(liveIncidents);" + m.group(1), label="plot incidents on map")

open(path, "w", encoding="utf-8").write(s)
print("Done ->", path, "(backup:", path + ".bak)")
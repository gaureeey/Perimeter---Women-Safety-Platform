# Perimeter---Women-Safety-Platform
A community-based women protection and emergency response platform featuring Instagram-style feed, verified roles, smart SOS, and full case traceability.
# 🛡️ PERIMETER — Women Safety & Community Response Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-PostGIS-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostGIS">
  <img src="https://img.shields.io/badge/Firebase-FCM-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase FCM">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

> **An Instagram-style social safety network combining verified community posts, motion-triggered SOS alerts, geofenced radius response, and end-to-end case traceability.**

---

## 📌 Executive Summary

Traditional personal safety apps rely on static SMS alerts that terminate as soon as a button is pressed, leading to high false-alarm rates and no post-trigger accountability. **PERIMETER** bridges the gap between everyday social media and emergency response. 

By unifying **Citizen Users, Verified Volunteers, Credentialed Journalists, and Local Police** into one Python-powered platform, PERIMETER ensures rapid, location-aware assistance with complete auditability.

---

## ✨ Key Features At A Glance

| Feature | Description |
| :--- | :--- |
| **📱 Social Safety Feed** | Share safety updates, stories, and location alerts with verified badges (`Police Verified`, `Verified Reporter`, `Volunteer`). |
| **🚨 Motion Shake SOS** | Hands-free emergency trigger using smartphone accelerometer data ($g$-force debouncing) alongside an in-app hold button. |
| **👥 4-User Governance** | Tailored dashboards and permissions for Citizens, Volunteers, Journalists, and Police. |
| **🗺️ Geospatial Heatmaps** | Real-time incident density mapping that automatically warns users upon entering flagged high-risk sectors. |
| **⚡ 5 km Geofenced Alerts** | Asynchronous push notifications dispatched instantly to verified responders within a configurable radius. |
| **📋 Universal Case Timeline** | Immutable audit logging that tracks every incident step (*Trigger ➔ Dispatch ➔ Acceptance ➔ Arrival ➔ Resolution*). |
| **🌸 Women Wellness Suite** | Client-side encrypted menstrual cycle tracking and private harassment journaling. |

---

## 👥 4-User Role Matrix
<!-- ROLE MATRIX COMPONENT -->
<div class="role-matrix-card">
  <div class="matrix-header">
    <h3>👥 PERIMETER 4-User Role & Permission Matrix</h3>
    <span class="matrix-tag">RBAC Security Layer</span>
  </div>
  
  <div class="matrix-grid">
    <!-- ROLE 1: CITIZEN USER -->
    <div class="matrix-col role-user">
      <div class="role-title">
        <span class="role-icon">👩</span> Citizen User
      </div>
      <ul class="role-permissions">
        <li><span class="check">✔</span> Social Feed & Stories</li>
        <li><span class="check">✔</span> Motion Shake & SOS Trigger</li>
        <li><span class="check">✔</span> Safety Heatmap Navigation</li>
        <li><span class="check">✔</span> Vehicle Accident Reporting</li>
        <li><span class="check">✔</span> Encrypted Wellness Journal</li>
        <li><span class="cross">✖</span> Post Verification Badge</li>
        <li><span class="cross">✖</span> Emergency Case Closure</li>
      </ul>
    </div>

    <!-- ROLE 2: VOLUNTEER -->
    <div class="matrix-col role-volunteer">
      <div class="role-title">
        <span class="role-icon">🙋</span> Verified Volunteer
      </div>
      <ul class="role-permissions">
        <li><span class="check">✔</span> Social Feed & Stories</li>
        <li><span class="check">✔</span> 5km Radius Dispatch Alerts</li>
        <li><span class="check">✔</span> Live Trajectory Navigation</li>
        <li><span class="check">✔</span> Log Arrival Timestamp</li>
        <li><span class="check">✔</span> Volunteer Badge on Posts</li>
        <li><span class="cross">✖</span> Edit Official Case Status</li>
        <li><span class="cross">✖</span> Publish Police Bulletins</li>
      </ul>
    </div>

    <!-- ROLE 3: JOURNALIST -->
    <div class="matrix-col role-journalist">
      <div class="role-title">
        <span class="role-icon">📰</span> Verified Journalist
      </div>
      <ul class="role-permissions">
        <li><span class="check">✔</span> Social Feed & Stories</li>
        <li><span class="check">✔</span> Verified Reporter Badge</li>
        <li><span class="check">✔</span> Link Press Notes to Case IDs</li>
        <li><span class="check">✔</span> Publish Newsroom Bulletins</li>
        <li><span class="check">✔</span> Public Case Archive Search</li>
        <li><span class="cross">✖</span> Accept Emergency Dispatch</li>
        <li><span class="cross">✖</span> Close Police Investigation</li>
      </ul>
    </div>

    <!-- ROLE 4: POLICE -->
    <div class="matrix-col role-police">
      <div class="role-title">
        <span class="role-icon">🚔</span> City Police
      </div>
      <ul class="role-permissions">
        <li><span class="check">✔</span> Priority SOS Command Desk</li>
        <li><span class="check">✔</span> Dispatch Patrol Units</li>
        <li><span class="check">✔</span> Issue Official Wanted Notices</li>
        <li><span class="check">✔</span> Full Case Timeline Authority</li>
        <li><span class="check">✔</span> Officially Resolve & Lock Case</li>
        <li><span class="check">✔</span> Police Verification Badge</li>
        <li><span class="check">✔</span> Access Complete Audit Logs</li>
      </ul>
    </div>
  </div>
</div>

<style>
  .role-matrix-card {
    background: #FFFFFF;
    border: 1px solid #E3E6F0;
    border-radius: 16px;
    padding: 24px;
    margin: 24px 0;
    font-family: 'Inter', sans-serif;
  }
  .matrix-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  .matrix-header h3 {
    font-size: 16px;
    font-weight: 800;
    color: #1B1F3B;
  }
  .matrix-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    background: #EEF1FB;
    color: #0F6E6E;
    padding: 4px 10px;
    border-radius: 100px;
    font-weight: 600;
  }
  .matrix-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
  .matrix-col {
    background: #F7F8FC;
    border: 1px solid #E3E6F0;
    border-radius: 12px;
    padding: 16px;
  }
  .role-title {
    font-size: 14px;
    font-weight: 700;
    color: #1B1F3B;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    border-bottom: 1px solid #E3E6F0;
    padding-bottom: 8px;
  }
  .role-permissions {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .role-permissions li {
    font-size: 12px;
    color: #5B6178;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .check { color: #0F6E6E; font-weight: bold; }
  .cross { color: #FF5A5F; font-weight: bold; }

  /* Role specific highlights */
  .role-user { border-top: 3px solid #1B1F3B; }
  .role-volunteer { border-top: 3px solid #D97706; }
  .role-journalist { border-top: 3px solid #0F6E6E; }
  .role-police { border-top: 3px solid #FF5A5F; }

  @media (max-width: 900px) {
    .matrix-grid { grid-template-columns: 1fr; }
  }
</style>

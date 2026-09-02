import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

# Set high DPI for crisp graphics
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

TEMPLATE_PATH = r"resources/Review-1 TEMPLATE_MINI PROJECT CSE7102.pptx"
OUTPUT_PATH = r"resources/PERIMETER_Review_1_Presentation.pptx"

# 1. Generate Crisp System Architecture Diagram
def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 6.8), facecolor='#0B0E1B')
    ax.set_facecolor('#0B0E1B')
    ax.axis('off')

    # Color Palette
    c_client = '#3B82F6'
    c_api = '#8B5CF6'
    c_engine = '#0F6E6E'
    c_data = '#D97706'
    c_accent = '#FF5A5F'
    c_text = '#F8FAFC'
    c_sub = '#94A3B8'

    # Title
    ax.text(6, 6.4, "PERIMETER — 4-TIER SYSTEM ARCHITECTURE", fontsize=16, fontweight='bold', color='#FFFFFF', ha='center', va='center')

    # Layer 1: Client Layer
    rect1 = patches.FancyBboxPatch((0.5, 4.4), 11, 1.4, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor='#171D36', edgecolor=c_client, linewidth=2)
    ax.add_patch(rect1)
    ax.text(0.8, 5.5, "1. CLIENT INTERACTION LAYER", fontsize=11, fontweight='bold', color=c_client)
    
    # Sub-boxes in Layer 1
    clients = [
        ("👩 Citizen User App", "Native Android (Java)\nMotion Shake SOS · Feed", 0.8, 4.6),
        ("🙋 Volunteer Console", "Web / Mobile Interface\n5km Dispatch Radar · HUD", 3.6, 4.6),
        ("📰 Press Desk", "Web Console (HTML5/JS)\nVerified Case Linking", 6.4, 4.6),
        ("🚔 Police Command", "Web Command Center\nPatrol & Case Resolution", 9.2, 4.6),
    ]
    for title, desc, x, y in clients:
        box = patches.FancyBboxPatch((x, y), 2.5, 0.75, boxstyle="round,pad=0.05,rounding_size=0.08", facecolor='#222B4D', edgecolor='rgba(255,255,255,0.15)', linewidth=1)
        ax.add_patch(box)
        ax.text(x + 1.25, y + 0.52, title, fontsize=9, fontweight='bold', color='#FFFFFF', ha='center')
        ax.text(x + 1.25, y + 0.22, desc, fontsize=7.5, color=c_sub, ha='center')

    # Arrow 1
    ax.annotate('', xy=(6, 4.1), xytext=(6, 4.4), arrowprops=dict(arrowstyle="->", color=c_accent, lw=2.5))
    ax.text(6.4, 4.25, "HTTPS / REST API / OAuth2 JWT", fontsize=8, color='#5EEAD4', fontweight='bold')

    # Layer 2: API Gateway & Security
    rect2 = patches.FancyBboxPatch((0.5, 3.0), 11, 0.95, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor='#1E1B38', edgecolor=c_api, linewidth=2)
    ax.add_patch(rect2)
    ax.text(0.8, 3.7, "2. API GATEWAY & RBAC SECURITY (Python FastAPI)", fontsize=11, fontweight='bold', color=c_api)
    ax.text(6, 3.3, "• JWT Token Verification  • Role-Based Access Interceptor (Citizen / Volunteer / Journalist / Police / Admin)  • CORS Middleware", 
            fontsize=8.5, color=c_text, ha='center')

    # Arrow 2
    ax.annotate('', xy=(6, 2.7), xytext=(6, 3.0), arrowprops=dict(arrowstyle="->", color=c_accent, lw=2.5))
    ax.text(6.4, 2.85, "Async Event Dispatch", fontsize=8, color='#FBBF24', fontweight='bold')

    # Layer 3: Core Services Engine
    rect3 = patches.FancyBboxPatch((0.5, 1.6), 11, 0.95, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor='#0D2626', edgecolor=c_engine, linewidth=2)
    ax.add_patch(rect3)
    ax.text(0.8, 2.3, "3. CORE REAL-TIME SERVICES ENGINE", fontsize=11, fontweight='bold', color='#2DD4BF')
    
    engines = [
        ("Accelerometer Debouncer", "Triple-shake g-force filter"),
        ("PostGIS Geofence Router", "ST_DWithin 5km radius"),
        ("Heatmap Density Aggregator", "Dynamic risk scoring"),
        ("Universal Case Timeline", "Immutable incident auditing")
    ]
    for idx, (etitle, edesc) in enumerate(engines):
        ex = 0.8 + idx * 2.8
        ax.text(ex + 1.25, 1.95, f"⚙ {etitle}", fontsize=8.5, fontweight='bold', color='#FFFFFF', ha='center')
        ax.text(ex + 1.25, 1.72, edesc, fontsize=7.5, color='#99F6E4', ha='center')

    # Arrow 3
    ax.annotate('', xy=(6, 1.3), xytext=(6, 1.6), arrowprops=dict(arrowstyle="->", color=c_accent, lw=2.5))

    # Layer 4: Data & Realtime Persistence Layer
    rect4 = patches.FancyBboxPatch((0.5, 0.2), 11, 0.95, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor='#2B1D0E', edgecolor=c_data, linewidth=2)
    ax.add_patch(rect4)
    ax.text(0.8, 0.9, "4. DATA & REAL-TIME NOTIFICATION LAYER", fontsize=11, fontweight='bold', color=c_data)
    ax.text(6, 0.5, "• PostgreSQL + PostGIS (Spatial Geometries & Schemas)  • Redis & Celery (Async Dispatch Queues)  • Firebase Cloud Messaging (FCM High-Priority Push)", 
            fontsize=8.5, color=c_text, ha='center')

    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.8)
    plt.tight_layout()
    os.makedirs("resources/diagrams", exist_ok=True)
    plt.savefig("resources/diagrams/architecture_diagram.png", bbox_inches='tight', facecolor='#0B0E1B')
    plt.close()
    print("Architecture diagram created successfully.")

# 2. Generate Professional Gantt Chart
def generate_gantt_chart():
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor='#0B0E1B')
    ax.set_facecolor('#111528')

    tasks = [
        ("1. Literature Survey & Requirement Analysis", 1, 3, '#8B5CF6'),
        ("2. Architecture Design & Database Schemas (PostGIS)", 3, 5, '#3B82F6'),
        ("3. UI/UX Prototyping & 4-Role Dashboards", 4, 7, '#0F6E6E'),
        ("4. FastAPI Gateway, Auth & RBAC Interceptors", 6, 9, '#10B981'),
        ("5. Accelerometer Debouncing & SOS Trigger Logic", 8, 11, '#F59E0B'),
        ("6. PostGIS 5km Geofenced Dispatch Engine", 10, 13, '#EF4444'),
        ("7. Case Timeline Sync & Heatmap Visualizations", 12, 15, '#EC4899'),
        ("8. System Integration, Security Audit & Field Testing", 14, 16, '#6366F1')
    ]

    y_pos = np.arange(len(tasks))

    for idx, (name, start, end, color) in enumerate(tasks):
        duration = end - start
        ax.barh(idx, duration, left=start, height=0.55, align='center', color=color, alpha=0.9, edgecolor='#FFFFFF', linewidth=0.8)
        # Task name inside/beside bar
        ax.text(start + 0.15, idx, f"Week {start} - {end}", va='center', ha='left', color='#FFFFFF', fontweight='bold', fontsize=8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([t[0] for t in tasks], fontsize=9.5, fontweight='bold', color='#F8FAFC')
    ax.invert_yaxis()  # Top-down order

    ax.set_xlabel("Project Timeline (Weeks)", fontsize=10, fontweight='bold', color='#94A3B8')
    ax.set_title("PERIMETER — WORK SCHEDULE & GANTT MILESTONES", fontsize=13, fontweight='bold', color='#FFFFFF', pad=14)

    ax.set_xlim(0, 17)
    ax.set_xticks(range(1, 17))
    ax.set_xticklabels([f"W{i}" for i in range(1, 17)], color='#94A3B8', fontsize=9)

    # Gridlines
    ax.grid(axis='x', color='rgba(255,255,255,0.1)', linestyle='--', linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#334155')
    ax.spines['bottom'].set_color('#334155')
    ax.tick_params(colors='#94A3B8')

    plt.tight_layout()
    plt.savefig("resources/diagrams/gantt_chart.png", bbox_inches='tight', facecolor='#0B0E1B')
    plt.close()
    print("Gantt chart created successfully.")

if __name__ == "__main__":
    generate_architecture_diagram()
    generate_gantt_chart()

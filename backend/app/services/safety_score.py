"""
PERIMETER Platform - SafetyScoreService
Combines NCRB area-level baseline statistics, real Perimeter incidents,
incident severity, exponential time decay, and multi-year crime trends
into a normalized 0-100 Perimeter Safety Risk Score.
"""
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.crime import CrimeStatistic, AreaSafetyScore
from app.models.sos import SOSIncident
from app.models.case import IncidentCase
from app.db.spatial import haversine_distance_km

class SafetyScoreConfig:
    # Configurable weights across data sources
    WEIGHT_NCRB: float = 0.40
    WEIGHT_INCIDENTS: float = 0.45
    WEIGHT_TREND: float = 0.15

    # Incident severity multipliers
    SEVERITY_WEIGHTS = {
        "CRITICAL": 1.0,
        "HIGH": 0.75,
        "MEDIUM": 0.50,
        "MINOR": 0.25
    }

    # Half-life for exponential recency decay in days (incidents 30 days old have half influence)
    RECENCY_HALF_LIFE_DAYS: float = 30.0

    # Risk level threshold classifications
    THRESHOLD_LOWER: float = 40.0
    THRESHOLD_HIGH: float = 65.0

class SafetyScoreService:
    def __init__(self, db: Session, config: SafetyScoreConfig = None):
        self.db = db
        self.config = config or SafetyScoreConfig()

    def calculate_recency_decay(self, incident_time: datetime, now: datetime = None) -> float:
        """
        Calculates exponential time-decay factor between 0.0 and 1.0:
        decay = exp(-ln(2) * (age_days / half_life))
        """
        if not incident_time:
            return 0.5
        if now is None:
            now = datetime.utcnow()
        age_days = max(0.0, (now - incident_time).total_seconds() / 86400.0)
        decay_constant = math.log(2) / self.config.RECENCY_HALF_LIFE_DAYS
        return math.exp(-decay_constant * age_days)

    def get_ncrb_baseline_risk(self, lat: float, lng: float) -> Tuple[float, str, str]:
        """
        Finds the nearest NCRB district baseline risk and multi-year trend.
        Returns: (baseline_score_0_to_100, trend_label, area_name)
        """
        scores = self.db.query(AreaSafetyScore).all()
        if not scores:
            return (50.0, "STABLE", "Regional Sector")

        best_score = None
        min_dist = float("inf")
        for s in scores:
            dist = haversine_distance_km(lat, lng, s.latitude, s.longitude)
            if dist < min_dist:
                min_dist = dist
                best_score = s

        if best_score:
            return (best_score.ncrb_baseline_score or 50.0, best_score.crime_trend or "STABLE", best_score.area_name)
        return (50.0, "STABLE", "Regional Sector")

    def calculate_incident_risk(self, lat: float, lng: float, radius_km: float = 3.0) -> Tuple[float, int]:
        """
        Aggregates Perimeter platform incidents within radius,
        applying severity weighting and exponential recency decay.
        Returns: (incident_risk_0_to_100, incident_count)
        """
        incidents = self.db.query(SOSIncident).all()
        now = datetime.utcnow()
        weighted_sum = 0.0
        count_in_radius = 0

        for inc in incidents:
            dist = haversine_distance_km(lat, lng, inc.latitude, inc.longitude)
            if dist <= radius_km:
                count_in_radius += 1
                sev_weight = self.config.SEVERITY_WEIGHTS.get(inc.severity, 0.5)
                recency_decay = self.calculate_recency_decay(inc.created_at, now)
                # Distance attenuation: closer incidents have higher impact
                dist_factor = 1.0 - (dist / radius_km) * 0.5
                weighted_sum += sev_weight * recency_decay * dist_factor * 25.0

        # Normalize incident risk to 0-100 scale (saturates smoothly with more incidents)
        normalized_incident_risk = min(100.0, weighted_sum)
        return (normalized_incident_risk, count_in_radius)

    def calculate_trend_score(self, trend_label: str) -> float:
        """Translates multi-year crime trend into score (0 to 100)."""
        if trend_label == "INCREASING":
            return 80.0
        elif trend_label == "DECREASING":
            return 25.0
        return 50.0

    def compute_location_safety_score(self, lat: float, lng: float, radius_km: float = 3.0) -> Dict:
        """
        Computes authoritative combined Perimeter Safety Risk Score (0 - 100).
        """
        ncrb_baseline, trend_label, area_name = self.get_ncrb_baseline_risk(lat, lng)
        incident_risk, inc_count = self.calculate_incident_risk(lat, lng, radius_km)
        trend_score = self.calculate_trend_score(trend_label)

        # Weighted combination
        final_risk = (
            ncrb_baseline * self.config.WEIGHT_NCRB +
            incident_risk * self.config.WEIGHT_INCIDENTS +
            trend_score * self.config.WEIGHT_TREND
        )
        final_risk = round(min(100.0, max(0.0, final_risk)), 1)

        # Determine risk level
        if final_risk >= self.config.THRESHOLD_HIGH:
            risk_level = "HIGH_REPORTED_RISK"
            label = "Higher reported risk"
            color = "#EF4444"
        elif final_risk >= self.config.THRESHOLD_LOWER:
            risk_level = "MODERATE_REPORTED_RISK"
            label = "Moderate reported risk"
            color = "#F59E0B"
        else:
            risk_level = "LOWER_REPORTED_RISK"
            label = "Lower reported risk"
            color = "#10B981"

        return {
            "area": area_name,
            "coordinates": {"latitude": lat, "longitude": lng},
            "risk_score": final_risk,
            "risk_level": risk_level,
            "risk_label": label,
            "color_hex": color,
            "incident_count": inc_count,
            "crime_trend": trend_label,
            "ncrb_baseline_score": ncrb_baseline,
            "data_sources": ["Perimeter incidents", "NCRB Crime in India statistics"],
            "attribution": "Risk estimation uses Perimeter incident reports and publicly available NCRB crime statistics."
        }

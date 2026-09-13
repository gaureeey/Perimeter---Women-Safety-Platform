"""
PERIMETER Universal Case Timeline & Press Desk API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db.session import get_db
from app.models.case import IncidentCase, TimelineEvent, LinkedPressArticle
from app.schemas.case import CaseResponse, TimelineEntry, PressArticleLink

router = APIRouter(prefix="/case", tags=["Universal Case Timeline & Press Desk"])

def serialize_case(c: IncidentCase) -> CaseResponse:
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
    return CaseResponse(
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
    )

@router.get("/", response_model=List[CaseResponse])
def get_all_cases(db: Session = Depends(get_db)):
    """
    Retrieve all incident cases with timeline audit logs.
    """
    cases = db.query(IncidentCase).order_by(IncidentCase.opened_at.desc()).all()
    return [serialize_case(c) for c in cases]

@router.get("/{case_id}", response_model=CaseResponse)
def get_case_by_id(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific incident case timeline and press coverage.
    """
    c = db.query(IncidentCase).filter(IncidentCase.case_id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case ID not found.")
    return serialize_case(c)

@router.post("/{case_id}/timeline")
def add_timeline_event(case_id: str, entry: TimelineEntry, db: Session = Depends(get_db)):
    """
    Append an immutable event to the case timeline.
    """
    c = db.query(IncidentCase).filter(IncidentCase.case_id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case ID not found.")

    event = TimelineEvent(
        case_id=case_id,
        title=entry.title,
        description=entry.description,
        actor_role=entry.actor_role,
        actor_name=entry.actor_name,
        timestamp=entry.timestamp
    )
    db.add(event)
    db.commit()
    return {"status": "success", "message": f"Timeline event added to {case_id}."}

@router.post("/{case_id}/link-press")
def link_press_article(case_id: str, article: PressArticleLink, db: Session = Depends(get_db)):
    """
    Attach a verified press report or journalistic investigation to a case timeline.
    """
    c = db.query(IncidentCase).filter(IncidentCase.case_id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case ID not found.")

    link = LinkedPressArticle(
        case_id=case_id,
        article_id=article.article_id or f"art_{uuid.uuid4().hex[:4]}",
        title=article.title,
        outlet=article.outlet,
        journalist_name=article.journalist_name,
        url=article.url,
        published_at=article.published_at
    )
    db.add(link)

    # Also log in timeline that a press report was attached
    press_event = TimelineEvent(
        case_id=case_id,
        title="Press Investigation Linked",
        description=f"Article '{article.title}' by {article.journalist_name} ({article.outlet}) linked to case audit.",
        actor_role="journalist",
        actor_name=article.journalist_name
    )
    db.add(press_event)

    db.commit()
    return {"status": "success", "message": f"Press article '{article.title}' linked to {case_id}."}

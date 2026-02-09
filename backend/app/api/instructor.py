"""
Instructor Dashboard API Routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import csv
import io
from datetime import datetime

from app.db import get_session, Student, Attempt, Question, MetricsSnapshot
from app.agents import TeacherSupportAgent


router = APIRouter(prefix="/instructor", tags=["instructor"])


@router.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    """Get instructor dashboard analytics."""
    support = TeacherSupportAgent(session)
    analytics = support.get_analytics()
    
    return {
        "total_students": analytics.total_students,
        "struggling_students": analytics.struggling_students,
        "concept_heatmap": analytics.concept_heatmap,
        "misconception_clusters": [
            {
                "misconception": c.misconception,
                "student_count": len(c.students),
                "severity": c.severity,
                "recommended_intervention": c.recommended_intervention
            }
            for c in analytics.misconception_clusters
        ],
        "priority_students": analytics.priority_students[:10],
        "intervention_suggestions": analytics.intervention_suggestions
    }


@router.get("/students/{student_id}")
def get_student_detail(student_id: int, session: Session = Depends(get_session)):
    """Get detailed view of a specific student."""
    support = TeacherSupportAgent(session)
    detail = support.get_student_detail(student_id)
    
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return detail


@router.get("/students")
def list_students(
    page: int = 1,
    limit: int = 20,
    session: Session = Depends(get_session)
):
    """List all students with basic info."""
    offset = (page - 1) * limit
    
    students = session.exec(
        select(Student).offset(offset).limit(limit)
    ).all()
    
    total = len(session.exec(select(Student)).all())
    
    return {
        "students": [
            {
                "id": s.id,
                "username": s.username,
                "baseline_level": s.baseline_level.value if s.baseline_level else "medium",
                "pretest_completed": s.pretest_completed,
                "posttest_completed": s.posttest_completed,
                "current_concept": s.current_concept,
                "avg_mastery": sum(s.mastery_scores.values()) / max(len(s.mastery_scores), 1) if s.mastery_scores else 0
            }
            for s in students
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/export/attempts")
def export_attempts(
    anonymize: bool = True,
    session: Session = Depends(get_session)
):
    """Export attempts as CSV."""
    attempts = session.exec(select(Attempt)).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "attempt_id",
        "student_id" if not anonymize else "student_hash",
        "question_id",
        "concept",
        "is_correct",
        "misconceptions",
        "confidence",
        "timestamp"
    ])
    
    for a in attempts:
        question = session.get(Question, a.question_id)
        student_id = hash(a.student_id) if anonymize else a.student_id
        
        writer.writerow([
            a.id,
            student_id,
            a.question_id,
            question.concept if question else "",
            a.is_correct,
            ";".join(a.misconceptions or []),
            a.confidence_score,
            a.submitted_at.isoformat() if a.submitted_at else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attempts_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@router.get("/export/metrics")
def export_metrics(session: Session = Depends(get_session)):
    """Export research metrics summary."""
    from app.metrics.research import compute_all_metrics
    
    metrics = compute_all_metrics(session)
    
    # Save snapshot
    snapshot = MetricsSnapshot(
        snapshot_type="export",
        metrics=metrics,
        created_at=datetime.utcnow()
    )
    session.add(snapshot)
    session.commit()
    
    return metrics


@router.get("/export/students")
def export_students(
    anonymize: bool = True,
    session: Session = Depends(get_session)
):
    """Export student data as CSV."""
    students = session.exec(select(Student)).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "student_id" if not anonymize else "student_hash",
        "baseline_level",
        "is_control_group",
        "pretest_completed",
        "posttest_completed",
        "mastery_variables",
        "mastery_loops",
        "mastery_arrays",
        "mastery_functions",
        "avg_mastery"
    ])
    
    for s in students:
        student_id = hash(s.id) if anonymize else s.id
        mastery = s.mastery_scores or {}
        
        writer.writerow([
            student_id,
            s.baseline_level.value if s.baseline_level else "medium",
            s.is_control_group,
            s.pretest_completed,
            s.posttest_completed,
            mastery.get("variables", 0),
            mastery.get("loops", 0),
            mastery.get("arrays", 0),
            mastery.get("functions", 0),
            sum(mastery.values()) / max(len(mastery), 1)
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=students_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

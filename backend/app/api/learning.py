"""
Student Learning API Routes

Handles the adaptive learning loop for students.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session, Student, Question, Attempt, Plan, QuestionType
from app.agents import OrchestratorAgent, DiagnosticAgent
from app.sandbox import run_tests


router = APIRouter(tags=["learning"])

# Global orchestrator instance
_orchestrator = OrchestratorAgent()


# ─────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────

class AttemptRequest(BaseModel):
    student_id: int
    question_id: int
    response: str
    time_spent_seconds: Optional[int] = None


class AttemptResponse(BaseModel):
    attempt_id: int
    is_correct: bool
    misconceptions: List[str]
    feedback: str


class NextContentResponse(BaseModel):
    action: str
    concept: str
    reason: str
    content: Optional[dict] = None
    question: Optional[dict] = None


class ProgressResponse(BaseModel):
    current_concept: str
    mastery_scores: dict
    overall_mastery: float
    misconceptions_history: List[str]
    concepts_completed: List[str]


# ─────────────────────────────────────────────────────────────
# Pretest Routes
# ─────────────────────────────────────────────────────────────

PRETEST_QUESTION_LIMIT = 5
POSTTEST_QUESTION_LIMIT = 5


@router.get("/pretest")
def get_pretest(session: Session = Depends(get_session)):
    """Get pretest questions (max 5)."""
    all_pretest = session.exec(
        select(Question).where(Question.is_pretest == True).order_by(Question.id)
    ).all()
    questions = all_pretest[:PRETEST_QUESTION_LIMIT]
    print(f"[Pretest] Returning {len(questions)} of {len(all_pretest)} pretest questions (limit={PRETEST_QUESTION_LIMIT})")
    
    if not questions:
        return JSONResponse(
            content={"questions": [], "message": "No pretest questions available"},
            headers={"Cache-Control": "no-store"}
        )
    
    payload = {
        "questions": [
            {
                "id": q.id,
                "type": q.question_type.value,
                "concept": q.concept,
                "prompt": q.prompt,
                "options": q.options,
                "starter_code": q.starter_code
            }
            for q in questions
        ]
    }
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


@router.post("/pretest/submit")
def submit_pretest(
    student_id: int,
    responses: List[dict],
    session: Session = Depends(get_session)
):
    """Submit pretest responses and get initial assessment."""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    results = []
    diagnostic = DiagnosticAgent()
    
    for resp in responses:
        question_id = resp.get("question_id")
        answer = resp.get("response", "")
        
        question = session.get(Question, question_id)
        if not question:
            continue
        
        # Check correctness
        if question.question_type == QuestionType.MCQ:
            is_correct = answer.upper() == question.correct_answer.upper()
            test_output = None
        else:
            # Coding question - run tests
            test_result = run_tests(answer, question.test_cases or {"tests": []})
            is_correct = test_result.get("all_passed", False)
            test_output = str(test_result)
        
        # Diagnose if incorrect
        misconceptions = []
        confidence = 0.0
        if not is_correct:
            diagnosis = diagnostic.diagnose(
                question_prompt=question.prompt,
                student_response=answer,
                correct_answer=question.correct_answer or question.solution or "",
                concept=question.concept,
                test_output=test_output
            )
            misconceptions = diagnosis.misconceptions
            confidence = diagnosis.confidence
        
        # Create attempt record
        attempt = Attempt(
            student_id=student_id,
            question_id=question_id,
            response=answer,
            is_correct=is_correct,
            misconceptions=misconceptions,
            confidence_score=confidence,
            submitted_at=datetime.utcnow()
        )
        session.add(attempt)
        
        results.append({
            "question_id": question_id,
            "is_correct": is_correct,
            "misconceptions": misconceptions
        })
        
        # Update initial mastery
        current_mastery = student.mastery_scores.get(question.concept, 0.5)
        new_mastery = current_mastery * 0.7 + (1.0 if is_correct else 0.0) * 0.3
        student.mastery_scores[question.concept] = new_mastery
    
    # Mark pretest complete and set starting concept
    student.pretest_completed = True
    
    # Find weakest concept to start with
    if student.mastery_scores:
        weakest = min(student.mastery_scores.items(), key=lambda x: x[1])
        student.current_concept = weakest[0]
    else:
        student.current_concept = "variables"
    
    session.add(student)
    session.commit()
    
    return {
        "pretest_completed": True,
        "results": results,
        "starting_concept": student.current_concept,
        "initial_mastery": student.mastery_scores
    }


# ─────────────────────────────────────────────────────────────
# Adaptive Learning Routes
# ─────────────────────────────────────────────────────────────

@router.get("/learn/{student_id}", response_model=NextContentResponse)
def get_next_content(student_id: int, session: Session = Depends(get_session)):
    """Get the next learning content/question for a student."""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.pretest_completed:
        raise HTTPException(status_code=400, detail="Complete pretest first")
    
    # Get last attempt if any
    last_attempt = session.exec(
        select(Attempt)
        .where(Attempt.student_id == student_id)
        .order_by(Attempt.submitted_at.desc())
    ).first()
    
    # Get orchestrator decision
    decision = _orchestrator.decide_next_action(student, last_attempt)
    
    # Save plan
    plan = Plan(
        student_id=student_id,
        action=decision.action,
        concept=decision.concept,
        reason=decision.reason,
        content=decision.content or decision.question,
        created_at=datetime.utcnow()
    )
    session.add(plan)
    
    # Update student's current concept
    student.current_concept = decision.concept
    session.add(student)
    session.commit()
    
    return NextContentResponse(
        action=decision.action.value,
        concept=decision.concept,
        reason=decision.reason,
        content=decision.content,
        question=decision.question
    )


@router.post("/attempt", response_model=AttemptResponse)
def submit_attempt(request: AttemptRequest, session: Session = Depends(get_session)):
    """Submit an attempt on a question."""
    student = session.get(Student, request.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    question = session.get(Question, request.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Evaluate response
    test_output = None
    if question.question_type == QuestionType.MCQ:
        is_correct = request.response.upper() == (question.correct_answer or "").upper()
    else:
        # Coding - run tests
        test_result = run_tests(
            request.response, 
            question.test_cases or {"tests": []}
        )
        is_correct = test_result.get("all_passed", False)
        test_output = str(test_result.get("results", []))
    
    # Diagnose misconceptions
    misconceptions = []
    confidence = 0.0
    feedback = "Correct! Well done." if is_correct else "Not quite right."
    
    if not is_correct:
        diagnostic = DiagnosticAgent()
        diagnosis = diagnostic.diagnose(
            question_prompt=question.prompt,
            student_response=request.response,
            correct_answer=question.correct_answer or question.solution or "",
            concept=question.concept,
            test_output=test_output
        )
        misconceptions = diagnosis.misconceptions
        confidence = diagnosis.confidence
        
        if misconceptions:
            feedback = f"Review these concepts: {', '.join(misconceptions[:2])}"
    
    # Create attempt record
    attempt = Attempt(
        student_id=request.student_id,
        question_id=request.question_id,
        response=request.response,
        is_correct=is_correct,
        execution_result={"test_output": test_output} if test_output else None,
        misconceptions=misconceptions,
        confidence_score=confidence,
        time_spent_seconds=request.time_spent_seconds,
        submitted_at=datetime.utcnow()
    )
    session.add(attempt)
    
    # Update mastery
    current = student.mastery_scores.get(question.concept, 0.5)
    alpha = 0.3
    student.mastery_scores[question.concept] = current * (1 - alpha) + (1.0 if is_correct else 0.0) * alpha
    session.add(student)
    
    session.commit()
    session.refresh(attempt)
    
    return AttemptResponse(
        attempt_id=attempt.id,
        is_correct=is_correct,
        misconceptions=misconceptions,
        feedback=feedback
    )


@router.get("/progress/{student_id}", response_model=ProgressResponse)
def get_progress(student_id: int, session: Session = Depends(get_session)):
    """Get student progress and mastery data."""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    progress = _orchestrator.get_student_progress(student)
    
    return ProgressResponse(
        current_concept=progress["current_concept"],
        mastery_scores=progress["mastery_scores"],
        overall_mastery=progress["overall_mastery"],
        misconceptions_history=progress["misconceptions_history"],
        concepts_completed=progress["concepts_completed"]
    )


# ─────────────────────────────────────────────────────────────
# Posttest Routes
# ─────────────────────────────────────────────────────────────

@router.get("/posttest")
def get_posttest(session: Session = Depends(get_session)):
    """Get posttest questions (max 5)."""
    all_posttest = session.exec(
        select(Question).where(Question.is_posttest == True).order_by(Question.id)
    ).all()
    questions = all_posttest[:POSTTEST_QUESTION_LIMIT]
    
    return {
        "questions": [
            {
                "id": q.id,
                "type": q.question_type.value,
                "concept": q.concept,
                "prompt": q.prompt,
                "options": q.options,
                "starter_code": q.starter_code
            }
            for q in questions
        ]
    }


@router.post("/posttest/submit")
def submit_posttest(
    student_id: int,
    responses: List[dict],
    session: Session = Depends(get_session)
):
    """Submit posttest and get final results."""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    results = []
    correct_count = 0
    
    for resp in responses:
        question_id = resp.get("question_id")
        answer = resp.get("response", "")
        
        question = session.get(Question, question_id)
        if not question:
            continue
        
        if question.question_type == QuestionType.MCQ:
            is_correct = answer.upper() == (question.correct_answer or "").upper()
        else:
            test_result = run_tests(answer, question.test_cases or {"tests": []})
            is_correct = test_result.get("all_passed", False)
        
        if is_correct:
            correct_count += 1
        
        # Record attempt
        attempt = Attempt(
            student_id=student_id,
            question_id=question_id,
            response=answer,
            is_correct=is_correct,
            misconceptions=[],
            confidence_score=1.0 if is_correct else 0.0,
            submitted_at=datetime.utcnow()
        )
        session.add(attempt)
        
        results.append({
            "question_id": question_id,
            "is_correct": is_correct
        })
    
    student.posttest_completed = True
    session.add(student)
    session.commit()
    
    return {
        "posttest_completed": True,
        "results": results,
        "score": correct_count,
        "total": len(results),
        "percentage": (correct_count / max(len(results), 1)) * 100,
        "final_mastery": student.mastery_scores
    }

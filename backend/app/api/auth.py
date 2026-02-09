"""
Authentication API Routes
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
import hashlib

from app.db import get_session, Student, BaselineLevel


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str
    baseline_level: str = "medium"  # For new registrations


class LoginResponse(BaseModel):
    student_id: int
    username: str
    baseline_level: str
    is_new: bool
    pretest_completed: bool


class InstructorLoginRequest(BaseModel):
    username: str
    password: str


def _hash_password(password: str) -> str:
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, session: Session = Depends(get_session)):
    """Login or register a student."""
    # Try to find existing student
    statement = select(Student).where(Student.username == request.username)
    student = session.exec(statement).first()
    
    if student:
        # Verify password
        if student.password_hash != _hash_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        student.last_login = datetime.utcnow()
        session.add(student)
        session.commit()
        
        return LoginResponse(
            student_id=student.id,
            username=student.username,
            baseline_level=student.baseline_level.value,
            is_new=False,
            pretest_completed=student.pretest_completed
        )
    else:
        # Create new student
        try:
            baseline = BaselineLevel(request.baseline_level)
        except ValueError:
            baseline = BaselineLevel.MEDIUM
        
        student = Student(
            username=request.username,
            password_hash=_hash_password(request.password),
            baseline_level=baseline,
            last_login=datetime.utcnow(),
            mastery_scores={}
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        
        return LoginResponse(
            student_id=student.id,
            username=student.username,
            baseline_level=student.baseline_level.value,
            is_new=True,
            pretest_completed=False
        )


@router.post("/instructor/login")
def instructor_login(request: InstructorLoginRequest):
    """Login as instructor (simplified - uses fixed credentials)."""
    # For MVP, use simple hardcoded credentials
    if request.username == "instructor" and request.password == "teach123":
        return {
            "success": True,
            "role": "instructor",
            "message": "Welcome, Instructor!"
        }
    raise HTTPException(status_code=401, detail="Invalid instructor credentials")

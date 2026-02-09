"""Database models for the Agentic Copilot system."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from enum import Enum


class BaselineLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionType(str, Enum):
    TEACH = "teach"
    TEST = "test"
    RETEACH = "reteach"
    REVIEW = "review"
    ADVANCE = "advance"


class QuestionType(str, Enum):
    MCQ = "mcq"
    CODING = "coding"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ─────────────────────────────────────────────────────────────
# Student Model
# ─────────────────────────────────────────────────────────────
class Student(SQLModel, table=True):
    """Student model with mastery tracking."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    baseline_level: BaselineLevel = Field(default=BaselineLevel.MEDIUM)
    is_control_group: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Mastery scores (JSON: concept -> score)
    mastery_scores: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Current state
    current_concept: Optional[str] = None
    pretest_completed: bool = Field(default=False)
    posttest_completed: bool = Field(default=False)
    
    # Relationships
    attempts: List["Attempt"] = Relationship(back_populates="student")
    plans: List["Plan"] = Relationship(back_populates="student")


# ─────────────────────────────────────────────────────────────
# Question Model
# ─────────────────────────────────────────────────────────────
class Question(SQLModel, table=True):
    """Question model for MCQ and coding problems."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Question type
    question_type: QuestionType
    difficulty: DifficultyLevel
    
    # Content
    concept: str = Field(index=True)
    prompt: str
    
    # For MCQ
    options: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    correct_answer: Optional[str] = None
    
    # For Coding
    starter_code: Optional[str] = None
    test_cases: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    solution: Optional[str] = None
    
    # Metadata
    is_pretest: bool = Field(default=False)
    is_posttest: bool = Field(default=False)
    is_generated: bool = Field(default=False)
    
    # Relationships
    attempts: List["Attempt"] = Relationship(back_populates="question")


# ─────────────────────────────────────────────────────────────
# Attempt Model
# ─────────────────────────────────────────────────────────────
class Attempt(SQLModel, table=True):
    """Student attempt on a question."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign keys
    student_id: int = Field(foreign_key="student.id")
    question_id: int = Field(foreign_key="question.id")
    
    # Response
    response: str
    is_correct: bool
    
    # For coding
    execution_result: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Diagnostic results
    misconceptions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    confidence_score: float = Field(default=0.0)
    
    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_seconds: Optional[int] = None
    
    # Relationships
    student: Optional[Student] = Relationship(back_populates="attempts")
    question: Optional[Question] = Relationship(back_populates="attempts")


# ─────────────────────────────────────────────────────────────
# Plan Model (Intervention Plans)
# ─────────────────────────────────────────────────────────────
class Plan(SQLModel, table=True):
    """Intervention plan for a student."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    student_id: int = Field(foreign_key="student.id")
    
    # Plan details
    action: ActionType
    concept: str
    reason: str
    
    # Content (micro-lesson, etc.)
    content: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Status
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Relationships
    student: Optional[Student] = Relationship(back_populates="plans")


# ─────────────────────────────────────────────────────────────
# Metrics Snapshot
# ─────────────────────────────────────────────────────────────
class MetricsSnapshot(SQLModel, table=True):
    """Snapshot of computed metrics."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    snapshot_type: str  # "daily", "experiment", "manual"
    
    # Metrics data
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# LLM Log
# ─────────────────────────────────────────────────────────────
class LLMLog(SQLModel, table=True):
    """Log of LLM interactions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Agent info
    agent_name: str
    
    # Request/Response
    prompt: str
    system_prompt: Optional[str] = None
    response: str
    
    # Metadata
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────
# Concept Graph Node (not a table, just a data model)
# ─────────────────────────────────────────────────────────────
class ConceptNode(SQLModel):
    """A node in the concept graph."""
    id: str
    name: str
    description: str
    prerequisites: List[str] = []
    misconceptions: List[str] = []

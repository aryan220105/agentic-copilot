"""
Agentic Learning Copilot - FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

from app.db import create_db_and_tables, engine, get_session
from app.db.models import Student, Question, Attempt, BaselineLevel, QuestionType, DifficultyLevel
from app.api import auth_router, learning_router, instructor_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    create_db_and_tables()
    seed_database()
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="Agentic Learning Copilot",
    description="AI-Based Adaptive Assessment and Remedial Learning System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(instructor_router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Agentic Learning Copilot",
        "version": "1.0.0",
        "llm_mode": settings.LLM_MODE,
        "status": "running"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def seed_database():
    """Seed the database with initial content."""
    from sqlmodel import Session, select
    
    with Session(engine) as session:
        # Check if already seeded
        existing = session.exec(select(Question)).first()
        if existing:
            return  # Already seeded
        
        # Load seed questions - check both paths (from backend/ and from project root)
        seed_path = "../data/seed/questions.json"
        if not os.path.exists(seed_path):
            seed_path = "data/seed/questions.json"
        if not os.path.exists(seed_path):
            print("No seed data found, skipping...")
            return
        
        with open(seed_path, "r") as f:
            data = json.load(f)
        
        # Seed MCQ questions
        for q in data.get("mcq_questions", []):
            question = Question(
                question_type=QuestionType.MCQ,
                difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                concept=q.get("concept", "variables"),
                prompt=q.get("prompt", ""),
                options=q.get("options", {}),
                correct_answer=q.get("correct_answer", ""),
                is_pretest=q.get("is_pretest", False),
                is_posttest=q.get("is_posttest", False),
                is_generated=False
            )
            session.add(question)
        
        # Seed coding questions
        for q in data.get("coding_questions", []):
            question = Question(
                question_type=QuestionType.CODING,
                difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                concept=q.get("concept", "variables"),
                prompt=q.get("prompt", ""),
                starter_code=q.get("starter_code", ""),
                test_cases=q.get("test_cases", {}),
                solution=q.get("solution", ""),
                is_pretest=False,
                is_posttest=False,
                is_generated=False
            )
            session.add(question)
        
        session.commit()
        print(f"Seeded {len(data.get('mcq_questions', []))} MCQs and {len(data.get('coding_questions', []))} coding questions")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

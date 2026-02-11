"""
Database seeding script
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlmodel import Session, SQLModel
from app.db.database import engine, create_db_and_tables
from app.db.models import Question, QuestionType, DifficultyLevel


def seed():
    """Seed the database with initial content."""
    from sqlmodel import select
    
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if already seeded
        existing = session.exec(select(Question)).first()
        if existing:
            print("Database already seeded, skipping. Use --force to re-seed.")
            return
    
    seed_path = "../data/seed/questions.json"
    if not os.path.exists(seed_path):
        print("No seed file found")
        return
    
    with open(seed_path, "r") as f:
        data = json.load(f)
    
    with Session(engine) as session:
        for q in data.get("mcq_questions", []):
            question = Question(
                question_type=QuestionType.MCQ,
                difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                concept=q.get("concept", "variables"),
                prompt=q.get("prompt", ""),
                options=q.get("options", {}),
                correct_answer=q.get("correct_answer", ""),
                is_pretest=q.get("is_pretest", False),
                is_posttest=q.get("is_posttest", False)
            )
            session.add(question)
        
        for q in data.get("coding_questions", []):
            question = Question(
                question_type=QuestionType.CODING,
                difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                concept=q.get("concept", "variables"),
                prompt=q.get("prompt", ""),
                starter_code=q.get("starter_code", ""),
                test_cases=q.get("test_cases", {}),
                solution=q.get("solution", "")
            )
            session.add(question)
        
        session.commit()
        mcq_count = len(data.get("mcq_questions", []))
        coding_count = len(data.get("coding_questions", []))
        print(f"Database seeded: {mcq_count} MCQs + {coding_count} coding questions")


def force_reseed():
    """Delete the database file entirely and re-seed from scratch."""
    from app.config import settings
    
    # Extract DB path from URL (sqlite:///./data/copilot.db -> ./data/copilot.db)
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted database: {db_path}")
        else:
            print(f"Database not found at {db_path}, creating fresh.")
    
    # Recreate tables and seed
    create_db_and_tables()
    _do_seed()


def _do_seed():
    """Internal seed without the duplicate check."""
    seed_path = "../data/seed/questions.json"
    if not os.path.exists(seed_path):
        print("No seed file found")
        return
    
    with open(seed_path, "r") as f:
        data = json.load(f)
    
    with Session(engine) as session:
        for q in data.get("mcq_questions", []):
            question = Question(
                question_type=QuestionType.MCQ,
                difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                concept=q.get("concept", "variables"),
                prompt=q.get("prompt", ""),
                options=q.get("options", {}),
                correct_answer=q.get("correct_answer", ""),
                is_pretest=q.get("is_pretest", False),
                is_posttest=q.get("is_posttest", False)
            )
            session.add(question)
        
        for q in data.get("coding_questions", []):
            question = Question(
                question_type=QuestionType.CODING,
                difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                concept=q.get("concept", "variables"),
                prompt=q.get("prompt", ""),
                starter_code=q.get("starter_code", ""),
                test_cases=q.get("test_cases", {}),
                solution=q.get("solution", "")
            )
            session.add(question)
        
        session.commit()
        mcq_count = len(data.get("mcq_questions", []))
        coding_count = len(data.get("coding_questions", []))
        print(f"Database seeded: {mcq_count} MCQs + {coding_count} coding questions")


if __name__ == "__main__":
    if "--force" in sys.argv:
        force_reseed()
    else:
        seed()

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
    create_db_and_tables()
    
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
        print("Database seeded successfully!")


if __name__ == "__main__":
    seed()

"""Database connection and session management."""
from sqlmodel import SQLModel, Session, create_engine
from app.config import settings
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}  # SQLite specific
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session

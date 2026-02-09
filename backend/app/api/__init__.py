"""API routes package initialization."""
from app.api.auth import router as auth_router
from app.api.learning import router as learning_router
from app.api.instructor import router as instructor_router

__all__ = ["auth_router", "learning_router", "instructor_router"]

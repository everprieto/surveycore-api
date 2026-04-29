"""
Database session dependency for FastAPI.
Ensures proper session cleanup via try/finally pattern.
"""
from typing import Generator
from sqlalchemy.orm import Session
from .database import Session as SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.
    Automatically closes the session after each request.

    Usage:
        @app.get("/route")
        def my_route(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

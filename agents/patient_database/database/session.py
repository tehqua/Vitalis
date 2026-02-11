"""Database session management."""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

from .config import engine


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session():
    """
    Context manager for database sessions.

    Yields:
        Session: SQLAlchemy session object

    Example:
        >>> with get_session() as session:
        ...     patient = session.query(Patient).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

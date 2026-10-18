"""Database session dependency wrapping ajnkit.db.session / SessionLocal."""

from collections.abc import Iterator
from sqlalchemy.orm import Session
from ajnkit.db import SessionLocal, session as ajn_session


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a SQLAlchemy session."""
    if SessionLocal is not None:
        with SessionLocal() as s:
            yield s
    else:
        yield from ajn_session()


__all__ = ["SessionLocal", "get_db"]

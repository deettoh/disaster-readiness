"""SQLAlchemy session and engine helpers for API data access."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool


def create_data_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for API data operations."""
    return create_engine(database_url, poolclass=NullPool)


def create_session_factory(
    database_url: str,
    *,
    engine: Engine | None = None,
) -> sessionmaker[Session]:
    """Create a configured session factory for ORM operations."""
    bound_engine = engine or create_data_engine(database_url)
    return sessionmaker(
        bind=bound_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

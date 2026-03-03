"""Shared ORM repository base helpers."""

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import create_session_factory


class _ORMRepositoryBase:
    """Base class for ORM repositories with shared session setup."""

    def __init__(
        self,
        *,
        database_url: str,
        engine: Engine | None = None,
    ) -> None:
        """Initialize shared database URL and session factory."""
        self._database_url = database_url
        self._session_factory: sessionmaker[Session] = create_session_factory(
            database_url,
            engine=engine,
        )


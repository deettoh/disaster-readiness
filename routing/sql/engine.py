"""Database engine helper for routing SQL modules."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_routing_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for routing queries."""
    return create_engine(database_url, pool_pre_ping=True)

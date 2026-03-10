"""Shared fixtures for E2E tests."""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")


@pytest.fixture(scope="module")
def db_engine():
    """Provides a real SQLAlchemy engine connected to the test/local database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set for E2E tests")
    engine = create_engine(db_url)
    yield engine
    engine.dispose()

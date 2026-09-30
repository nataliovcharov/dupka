import os

# tests use their own database so they never touch development data
# (set before anything imports the app settings)
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://dupka:dupka@localhost:5432/dupka_test",
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.rate_limit import limiter  # noqa: E402
from app.db.session import engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Bring the test database schema up to date once per test run."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def clean_reports(migrated_database):
    """Start every test with empty tables."""
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE reviews, reports, issues"))


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Every test starts with fresh upload counters."""
    limiter.reset()

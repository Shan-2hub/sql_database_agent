
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Load environment variables from project root
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/analytics.db"
)


def get_engine() -> Engine:
    """Create and return the SQLAlchemy database engine."""

    if DATABASE_URL.startswith("sqlite"):
        database_path = BASE_DIR / "data"
        database_path.mkdir(parents=True, exist_ok=True)

        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False
        )

    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )


engine = get_engine()

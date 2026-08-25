from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_environment() -> None:
    """Load base configuration followed by the selected environment overlay."""
    load_dotenv(PROJECT_ROOT / ".env")

    app_env = os.getenv("APP_ENV", "development")
    load_dotenv(PROJECT_ROOT / f".env.{app_env}", override=True)


load_environment()

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://order_resolver:order_resolver@localhost:5432/order_resolver"
)


def _to_psycopg_connection_url(database_url: str) -> str:
    """Convert the SQLAlchemy Postgres URL into a Psycopg connection URL."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )

    if database_url.startswith(("postgresql://", "postgres://")):
        return database_url

    raise ValueError("Checkpointing requires a PostgreSQL connection URL")


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    checkpoint_database_url: str = os.getenv("CHECKPOINT_DATABASE_URL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    def __post_init__(self) -> None:
        checkpoint_database_url = self.checkpoint_database_url or self.database_url
        object.__setattr__(
            self,
            "checkpoint_database_url",
            _to_psycopg_connection_url(checkpoint_database_url),
        )


settings = Settings()

"""Idempotent startup migration runner.

Because this project has no external migration tool (deploy just runs the app),
we apply the ordered SQL files under ``migrations/`` on startup so a fresh
database is brought fully up to date automatically.

Design:
- Files are discovered from the repo-level ``migrations/`` directory and applied
  in filename order (``001_...sql`` ... ``NNN_...sql``).
- Each file is executed as a whole SQL *script* via asyncpg's
  ``Connection.execute`` (simple-query protocol), so multiple statements and
  dollar-quoted function/trigger bodies (``$$ ... $$``) run intact. This is why
  we use a raw asyncpg connection rather than SQLAlchemy Core, which prepares
  statements and cannot run multi-statement scripts.
- Applied files are recorded in a ``schema_migrations`` table so each file runs
  at most once. The individual migrations are also written to be idempotent
  (``IF NOT EXISTS`` / ``ON CONFLICT``), so re-running is safe even without the
  ledger — the ledger just avoids needless re-execution.

Run this before :func:`skill_hub.db.bootstrap.bootstrap_auth`; the auth schema
is migration ``023`` and is applied here as part of the ordered set.
"""

import logging
from pathlib import Path

import asyncpg

from skill_hub.config.config import Config

logger = logging.getLogger(__name__)

# Repo layout: <root>/skill_hub/db/migrations.py -> <root>/migrations
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"

_LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def _asyncpg_dsn(database_url: str) -> str:
    """Normalize a SQLAlchemy/env database URL to a plain asyncpg DSN."""
    dsn = database_url
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif dsn.startswith("postgres://"):
        dsn = dsn.replace("postgres://", "postgresql://", 1)
    return dsn


def _discover_migration_files() -> list[Path]:
    """Return migration SQL files sorted by filename (numeric prefix order)."""
    if not MIGRATIONS_DIR.is_dir():
        logger.warning("Migrations directory not found: %s", MIGRATIONS_DIR)
        return []
    return sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda p: p.name)


async def run_migrations(config: Config) -> None:
    """Apply all pending SQL migrations in order (idempotent)."""
    if not config.has_database:
        logger.info("No database configured; skipping migrations")
        return

    files = _discover_migration_files()
    if not files:
        logger.info("No SQL migrations to apply")
        return

    conn = await asyncpg.connect(_asyncpg_dsn(config.database_url))
    try:
        ledger_existed = await conn.fetchval("SELECT to_regclass('schema_migrations')")
        await conn.execute(_LEDGER_DDL)

        # Baseline pre-existing databases. Migrations 001-019 predate the
        # idempotency convention (they use bare ``CREATE TABLE``), so blindly
        # replaying them against an already-populated DB would raise
        # ``DuplicateTableError``. If the ledger was just created but the schema
        # already exists (an environment provisioned before this runner), record
        # every current file as applied without running it — the schema is
        # assumed to already match. Fresh databases have no such table and fall
        # through to normal application.
        if not ledger_existed and not await conn.fetch(
            "SELECT filename FROM schema_migrations LIMIT 1"
        ):
            schema_present = await conn.fetchval("SELECT to_regclass('skills')")
            if schema_present:
                await conn.executemany(
                    "INSERT INTO schema_migrations (filename) VALUES ($1) "
                    "ON CONFLICT (filename) DO NOTHING",
                    [(f.name,) for f in files],
                )
                logger.info(
                    "Existing database detected; baselined %d migration(s) as "
                    "already applied",
                    len(files),
                )
                return

        applied = {
            r["filename"]
            for r in await conn.fetch("SELECT filename FROM schema_migrations")
        }

        pending = [f for f in files if f.name not in applied]
        if not pending:
            logger.info("Database schema up to date (%d migrations)", len(files))
            return

        for path in pending:
            sql = path.read_text(encoding="utf-8")
            logger.info("Applying migration: %s", path.name)
            # One transaction per file: the whole script and its ledger row
            # commit together, so a failure leaves a clean boundary.
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1) "
                    "ON CONFLICT (filename) DO NOTHING",
                    path.name,
                )

        logger.info("Applied %d migration(s)", len(pending))
    finally:
        await conn.close()

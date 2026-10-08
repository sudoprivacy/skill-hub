import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from skill_hub.models.assistant import Assistant
from skill_hub.models.skill import Base
from skill_hub.services.assistant_service import AssistantService


@asynccontextmanager
async def assistant_session(rows):
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL pagination tests")
    url = make_url(database_url)
    assert url.database == "skill_hub_test"
    assert url.host in {"localhost", "127.0.0.1", "postgres"}
    schema = "qa_pagination_" + uuid.uuid4().hex
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        execution_options={"schema_translate_map": {None: schema}},
    )
    try:
        async with engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.run_sync(Base.metadata.create_all)
        async with AsyncSession(engine, expire_on_commit=False) as session:
            session.add_all(
                Assistant(
                    id=uuid.UUID(int=row[0]),
                    name=f"qa-assistant-{row[0]}",
                    profession="QA",
                    sort_order=row[1],
                    created_at=row[2],
                    updated_at=row[2],
                    status=row[3],
                    tenant_id=row[4][0] if row[4] else None,
                    tenant_ids=row[4],
                )
                for row in rows
            )
            await session.commit()
            yield session
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()


def rows():
    now = datetime(2026, 5, 7, 17, 57, 36, 857884, tzinfo=timezone.utc)
    return [
        (9, 5, now - timedelta(days=1), 1, []),
        (8, 0, now, 1, []),
        (7, 0, now, 1, []),
        (6, 0, now - timedelta(seconds=1), 1, []),
        (5, 0, now, 0, []),
        (4, 0, now, 1, ["tenant-a", "tenant-b"]),
    ]


async def collect_pages(service, limit, **filters):
    cursor = None
    ids = []
    cursors = set()
    for _ in range(10):
        page = await service.list_all_cursor(cursor=cursor, limit=limit, **filters)
        batch = [int(assistant.id) for assistant in page["assistants"]]
        assert len(batch) <= limit
        assert not set(batch).intersection(ids), "A later page repeated earlier IDs"
        ids.extend(batch)
        if not page["has_more"]:
            assert page["next_cursor"] is None
            return ids
        cursor = page["next_cursor"]
        assert cursor and cursor not in cursors, "Pagination cursor did not advance"
        cursors.add(cursor)
    pytest.fail("Pagination did not terminate")


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_public_pages_preserve_priority_time_and_id_order(limit):
    async def verify():
        async with assistant_session(rows()) as session:
            assert await collect_pages(AssistantService(session), limit) == [9, 8, 7, 6]

    asyncio.run(verify())


def test_cursor_time_preserves_microseconds_and_timezone():
    async def verify():
        now = datetime(2026, 5, 7, 12, 30, tzinfo=timezone(timedelta(hours=5)))
        records = [
            (3, 0, now, 1, []),
            (2, 0, now - timedelta(microseconds=1), 1, []),
            (1, 0, now - timedelta(seconds=1), 1, []),
        ]
        async with assistant_session(records) as session:
            assert await collect_pages(AssistantService(session), 1) == [3, 2, 1]

    asyncio.run(verify())


def test_paginated_tenant_filter_excludes_public_and_other_tenants():
    async def verify():
        records = rows()
        now = records[0][2]
        records += [
            (3, 0, now, 1, ["tenant-b"]),
            (2, 0, now, 1, ["tenant-c"]),
        ]
        async with assistant_session(records) as session:
            assert await collect_pages(
                AssistantService(session), 1, tenant_id="tenant-b"
            ) == [4, 3]

    asyncio.run(verify())


def test_admin_pagination_can_include_pending_records():
    async def verify():
        async with assistant_session(rows()) as session:
            assert await collect_pages(
                AssistantService(session), 2, status=None
            ) == [9, 8, 7, 5, 6]

    asyncio.run(verify())

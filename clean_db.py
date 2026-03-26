import asyncio
from skill_hub.config.config import Config
from skill_hub.db.database import init_db, get_session
from sqlalchemy import text

async def main():
    config = Config()
    init_db(config)
    async with get_session() as session:
        await session.execute(text("DELETE FROM skill_versions;"))
        await session.execute(text("DELETE FROM skills WHERE name='test-skill';"))

asyncio.run(main())

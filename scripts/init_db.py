"""Create the application's tables in the database configured by DATABASE_URL.

This is intended for a fresh development database. ``create_all`` creates
missing tables but does not migrate or alter existing tables.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import Base, engine
from app.models.booking import Booking  # noqa: F401
from app.models.movie import Movie  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.showtime import Showtime  # noqa: F401
from app.models.user import User  # noqa: F401


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database tables are ready.")


if __name__ == "__main__":
    asyncio.run(main())

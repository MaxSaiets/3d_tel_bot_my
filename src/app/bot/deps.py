from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal


async def create_session() -> AsyncSession:
    return SessionLocal()


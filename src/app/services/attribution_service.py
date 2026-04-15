from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.users import UserRepository
from app.utils.deeplink import normalize_source_code


class AttributionService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

    async def save_start_source(self, user_id: int, raw_source_code: str | None) -> str | None:
        source_code = normalize_source_code(raw_source_code)
        if not source_code:
            return None
        await self.user_repo.save_attribution(user_id=user_id, source_code=source_code)
        return source_code


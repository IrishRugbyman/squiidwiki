from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def refresh_materialized_views(session: AsyncSession) -> None:
    for view in ("member_stats", "set_stats"):
        try:
            await session.execute(
                text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
            )
            await session.commit()
        except Exception:
            await session.rollback()

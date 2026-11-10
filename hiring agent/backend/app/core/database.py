from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all tables - used for development/testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Simple migration to ensure access_code exists on older DBs
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE assessment_configs ADD COLUMN access_code VARCHAR(12);"))
            await conn.execute(text("CREATE UNIQUE INDEX ix_assessment_configs_access_code ON assessment_configs (access_code);"))
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Migration configs skipped or failed: {e}")

        # If assessment_sessions still has the old access_code column, it will crash because of NOT NULL constraint
        try:
            from sqlalchemy import text
            result = await conn.execute(text("PRAGMA table_info(assessment_sessions)"))
            columns = [row[1] for row in result.fetchall()]
            if 'access_code' in columns:
                import logging
                logging.getLogger(__name__).warning("Found legacy access_code in assessment_sessions. Recreating candidate tables...")
                await conn.execute(text("DROP TABLE IF EXISTS candidate_answers;"))
                await conn.execute(text("DROP TABLE IF EXISTS assessment_results;"))
                await conn.execute(text("DROP TABLE IF EXISTS assessment_sessions;"))
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to migrate assessment_sessions: {e}")


async def drop_tables():
    """Drop all tables - used for testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

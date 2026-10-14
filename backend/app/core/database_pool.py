# import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from sqlalchemy.pool import QueuePool
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class DatabasePool:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self) -> None:
        if self.engine is not None:
            return

        database_url = settings.database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

        self.engine = create_async_engine(
            database_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database connection pool initialized")

    def get_session(self) -> AsyncSession:
        if self.session_factory is None:
            raise RuntimeError("Database pool has not been initialized")

        return self.session_factory()

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()

        self.engine = None
        self.session_factory = None


db_pool = DatabasePool()

async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with db_pool.get_session() as session:
        yield session

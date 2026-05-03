import contextlib
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from src.conf.config import config

logger = logging.getLogger(__name__)

class DatabaseSessionManager:
    def __init__(self, db_url: str):
        self._engine: AsyncEngine | None = create_async_engine(db_url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            self._engine, autocommit=False, autoflush=False
        )

    @contextlib.asynccontextmanager
    async def get_session(self):
        if self._session_maker is None:
            logger.warning("Database session is not initialized.")
            raise SQLAlchemyError("Database session is not initialized.")
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.warning("Failed to create a session.")
                raise e
            finally:
                await session.close()


database_session_manager = DatabaseSessionManager(config.DB_URL)


async def get_db_session():
    async with database_session_manager.get_session() as session:
        yield session

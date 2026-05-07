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
    """Manages the async SQLAlchemy engine and session factory lifecycle."""

    def __init__(self, db_url: str):
        """Create the async engine and session factory for the given database URL.

        Args:
            db_url: SQLAlchemy-compatible async connection string (e.g. ``postgresql+asyncpg://...``).
        """
        self._engine: AsyncEngine | None = create_async_engine(db_url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            self._engine, autocommit=False, autoflush=False
        )

    @contextlib.asynccontextmanager
    async def get_session(self):
        """Yield an async SQLAlchemy session, committing on success and rolling back on error.

        Raises:
            SQLAlchemyError: If the session factory has not been initialised.
            Exception: Re-raises any exception thrown inside the ``async with`` block.
        """
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
    """FastAPI dependency that yields a managed async database session.

    Yields:
        An :class:`sqlalchemy.ext.asyncio.AsyncSession` for the current request.
    """
    async with database_session_manager.get_session() as session:
        yield session

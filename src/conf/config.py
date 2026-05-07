from pydantic import ConfigDict, EmailStr, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or a .env file.

    PostgreSQL, Redis, JWT, SMTP, and Cloudinary credentials are all read here.
    ``DB_URL`` is assembled automatically via :meth:`assemble_db_url` after loading.
    """

    # POSTGRESQL
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_HOST: str
    POSTGRESQL_PORT: int
    POSTGRESQL_DB: str
    DB_URL: str | None = None

    # WEB SERVER
    WEB_SERVER_HOST: str
    WEB_SERVER_PORT: int

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_SECONDS: int
    REFRESH_TOKEN_EXPIRE_SECONDS: int

    # REDIS
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    USER_CACHE_TTL: int

    # MAIL
    MAIL_USERNAME: EmailStr = "example@example.com"
    MAIL_PASSWORD: str = ""
    MAIL_FROM: EmailStr = "example@example.com"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # CLOUDINARY
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        """Build and store the full async PostgreSQL URL from individual credentials.

        Returns:
            The updated Settings instance with ``DB_URL`` populated.
        """
        self.DB_URL = (
            f"postgresql+asyncpg://{self.POSTGRESQL_USER}:{self.POSTGRESQL_PASSWORD}"
            f"@{self.POSTGRESQL_HOST}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DB}"
        )
        return self


config = Settings()

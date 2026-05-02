from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator

class Settings(BaseSettings):
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

    # CLOUDINARY
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        self.DB_URL = (
            f"postgresql+asyncpg://{self.POSTGRESQL_USER}:{self.POSTGRESQL_PASSWORD}"
            f"@{self.POSTGRESQL_HOST}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DB}"
        )
        return self

config = Settings()
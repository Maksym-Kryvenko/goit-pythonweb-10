from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    DB_URL = f"postgresql+asyncpg://{os.getenv('POSTGRESQL_USER')}:{os.getenv('POSTGRESQL_PASSWORD')}@{os.getenv('POSTGRESQL_HOST')}:{os.getenv('POSTGRESQL_PORT')}/{os.getenv('POSTGRESQL_DB')}"


config = Config()
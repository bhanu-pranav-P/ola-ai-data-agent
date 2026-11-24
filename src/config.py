# Settings, loaded from .env (see .env.example)

import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ola_db"
    )

    # SQL agent: how many times the judge can send a query back for a rewrite
    max_sql_retries: int = 2
    # safety cap so a bad question can't pull the whole table into the prompt
    max_rows_to_show: int = 20


settings = Settings()

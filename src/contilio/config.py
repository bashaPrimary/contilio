from typing import Text

from pydantic import BaseModel

SERVICE_NAME = "CONTILIO Train Journey Planner"


class RequiredEnviron(BaseModel):
    """
    Represents all required environment variables and is used for automatic parsing/validation.
    """

    JP_SQLLITE_DB_FILE_NAME: Text
    JP_RUN_ALEMBIC_MIGRATIONS: bool
    TRANSPORT_API_APP_ID: Text
    TRANSPORT_API_APP_KEY: Text
    ALEMBIC_TRANSACTION_PER_MIGRATION: bool = True
    NUM_UVICORN_WORKERS: int = 1
    SERVICE_PORT: int = 5002
    ALEMBIC_DIRECTORY: Text = "journey_planner"

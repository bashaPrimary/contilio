import os
from logging import getLogger

import dotenv
from fastapi.applications import FastAPI

from contilio.api import service
from contilio.clients.transport_api import AppCreds, create_transportapi_client
from contilio.config import RequiredEnviron
from contilio.persistence.journey_planner import JourneyPlannerPersistenceFactory
from contilio.task_executor.executor import get_task_executor
from contilio.utils.db_connection import create_engine

logger = getLogger(__name__)


def init_app() -> FastAPI:
    dotenv.load_dotenv()
    env = RequiredEnviron.parse_obj(os.environ)

    jp_db_engine = create_engine(env)
    persistence_factory = JourneyPlannerPersistenceFactory(jp_db_engine)

    transportapi_client = create_transportapi_client(
        app_creds=AppCreds(app_id=env.TRANSPORT_API_APP_ID, app_key=env.TRANSPORT_API_APP_KEY)
    )

    app = service.get_app(
        persistence_factory=persistence_factory,
        transportapi_client=transportapi_client,
        task_executor=get_task_executor(max_workers=16),
    )

    return app

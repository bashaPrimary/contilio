import logging

from concurrent.futures._base import Executor
from typing import Optional

from contilio.clients.transport_api import TransportApiClient
from contilio.persistence.protocol import PersistenceFactory
from fastapi.applications import FastAPI
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter


from contilio.api.graph_ql.query import Query

from contilio.config import SERVICE_NAME
from contilio.task_executor.executor import get_task_executor

logger = logging.getLogger("uvicorn.error")


def _startup() -> None:
    logger.info("Starting up %s worker. Hello!", SERVICE_NAME)


SCHEMA = Schema(Query)


def get_app(
    persistence_factory: PersistenceFactory,
    transportapi_client: TransportApiClient,
    task_executor: Optional[Executor] = None,
) -> FastAPI:
    """Builds a FastAPI app with supplied dependencies"""
    task_executor_instance = task_executor or get_task_executor()

    app = FastAPI(
        title=SERVICE_NAME,
        task_executor=task_executor_instance,
        persistence_factory=persistence_factory,
        transportapi_client=transportapi_client,
    )

    def _shutdown() -> None:
        logger.info("Shutting down %s worker. Bye!", SERVICE_NAME)

    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)

    @app.get("/")
    def ping():
        return {"ping": "pong"}

    @app.get("/health")
    def health():
        return {"health": "I am feeling ok!!"}

    graphql_app = GraphQLRouter(SCHEMA)
    app.include_router(graphql_app, prefix="/graphql")

    return app

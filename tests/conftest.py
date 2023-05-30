"""
Fixtures defined here are automatically shared across all tests
under the tests directory.
Read more on conftest.py: https://docs.pytest.org/en/2.7.3/plugins.html
"""
import asyncio
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from logging import getLogger
from typing import Callable, Optional, Text
from unittest.mock import MagicMock, Mock

import dotenv
import pytest
from async_asgi_testclient import TestClient
from fastapi import FastAPI
from pytest import fixture
from requests import HTTPError, Response


from contilio.api.service import get_app
from contilio.config import RequiredEnviron
from contilio.persistence.in_memory import make_graph_persistence_factory
from contilio.task_executor.executor import get_task_executor

from contilio.clients.transport_api import TransportApiClient, TrainRoutePlan
from contilio.persistence import PersistenceFactory


logger = getLogger(__name__)


@pytest.fixture()
def graphql_client_helper(create_fastapi_client):
    """
    helper for writing graphql requests. Provides all headers and extraneous metadata in the
    post request required for a basic graphql call to the app.

    this function will handle raising errors if a graphql error is returned -- meaning that
    if you successfully make a graphql call and get a response back, you can be assured that
    the call did not fail
    """

    async def run(query, vars, app_args=None):
        app_args = app_args or {}
        async with create_fastapi_client(**app_args) as api_client:
            result = await api_client.post(
                "/graphql",
                json={"query": query, "variables": vars},
            )
            raise_for_graphql_error(result)
            return result.json()["data"]

    return run


@fixture(scope="function")
def mock_transportapi_client() -> TransportApiClient:
    async def get_train_route_plan(
        point_a: str, point_b: str, datetime_of_interest: datetime
    ) -> TrainRoutePlan:
        return TrainRoutePlan.from_dict(
            {
                "routes": [
                    {
                        "departure_datetime": (
                            datetime_of_interest + timedelta(minutes=5)
                        ).isoformat(),
                        "arrival_datetime": (
                            datetime_of_interest + timedelta(minutes=15)
                        ).isoformat(),
                    }
                ]
            }
        )

    client = MagicMock()
    client.get_train_route_plan.side_effect = get_train_route_plan
    return client


@fixture(scope="module")
def in_memory_persistence_factory() -> PersistenceFactory:
    return make_graph_persistence_factory()


@fixture(scope="session")
def task_executor_pool():
    """A simple fixture that creates a task executor at the beginning of test suite run.
    Use it whenever you need to call `get_app()` in your tests, so that no extra pools are created
    for individual test cases - it saves test time a bit.
    """
    with get_task_executor() as te:
        yield te


@fixture(scope="function")
def create_fastapi_client(
    task_executor_pool,
    in_memory_persistence_factory,
    mock_transportapi_client,
) -> Callable[[Optional[FastAPI]], TestClient]:
    def create_client(
        task_executor=task_executor_pool,
        persistence_factory=in_memory_persistence_factory,
        transportapi_client=mock_transportapi_client,
    ) -> TestClient:

        app = get_app(
            task_executor=task_executor,
            persistence_factory=persistence_factory,
            transportapi_client=transportapi_client,
        )

        return TestClient(app)

    yield create_client


class RaisedGraphQLError(Exception):
    pass


def raise_for_graphql_error(response: Response) -> None:
    try:
        response.raise_for_status()
    except HTTPError as e:
        errors = e.response.json()["errors"]
        raise RaisedGraphQLError(
            f"failed with errors: {','.join(error['message'] for error in errors)}"
        )


@contextmanager
def raises_graphql_error(expected_error_message: Text):
    try:
        yield
        raise Exception(f"expected graphql error with message '{expected_error_message}'")
    except HTTPError as e:
        errors = e.response.json()["errors"]
        assert errors
        error_message = errors[0]["message"]
        assert expected_error_message in error_message
    except RaisedGraphQLError as e:
        assert expected_error_message in str(e)


@fixture(scope="session")
def environment() -> RequiredEnviron:
    dotenv.load_dotenv()
    return RequiredEnviron.parse_obj(os.environ)

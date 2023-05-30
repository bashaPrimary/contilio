import pytest
from datetime import datetime

from contilio.api.graph_ql.query import DATETIME_FORMAT


datetime_of_interest = "2023-05-31 14:50"

journey_planner_query = f"""{{
                          journeyPlan(userInput:{{
                            routeCrsIds:[LVJ, LDY], datetimeOfInterest:"{datetime_of_interest}"
                          }}){{
                            arrivalTime
                          }}
                        }}"""


def parse_date(date_value: str):
    return datetime.strptime(date_value, DATETIME_FORMAT)


@pytest.mark.asyncio
async def test_query_response_from_transport_api(graphql_client_helper, mock_transportapi_client):
    result = await graphql_client_helper(
        journey_planner_query,
        {},
    )

    called_api_layer = mock_transportapi_client.get_train_route_plan.called
    assert called_api_layer

    response = result["journeyPlan"]["arrivalTime"]
    assert parse_date(response) > parse_date(datetime_of_interest)


@pytest.mark.asyncio
async def test_query_response_from_persistence(graphql_client_helper, mock_transportapi_client):
    identical_query_rerun = await graphql_client_helper(
        journey_planner_query,
        {},
    )

    called_persistence_layer = not mock_transportapi_client.get_train_route_plan.called
    assert called_persistence_layer

    response = identical_query_rerun["journeyPlan"]["arrivalTime"]
    assert parse_date(response) > parse_date(datetime_of_interest)

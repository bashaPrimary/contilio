import strawberry
from logging import getLogger

from datetime import datetime, timedelta
from dateutil import tz

from contilio.persistence import persistence_from_request_context
from contilio.task_executor.executor import make_awaitable
from contilio.api.graph_ql import errors
from contilio.api.graph_ql.inputs import RoutesInput
from contilio.clients.transport_api import (
    transport_api_client_from_request_context,
    TrainRoutePlan,
)
from contilio.persistence.protocol import Route
from contilio.utils.hasher import generate_hash

from strawberry.types import Info

logger = getLogger(__name__)

MAX_WAIT_TIME_IN_MINUTES = 60
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


@strawberry.type
class RouteResponse:
    arrival_time: str = strawberry.field(
        description="Arrival date time at the destination station"
    )


@strawberry.type
class Query:
    @strawberry.field
    async def journey_plan(self, user_input: RoutesInput, info: Info) -> RouteResponse:
        """
        The main resolver method for accepting user input to query journey plans.

        It's a bit convoluted in the sense it iterates over the station CRS codes provided by the user.

        First for a given sub route of the entire route, check if its hash exists already in the persistence.
        The sub route is the first given point to the destination in the current iteration, basically
        a sliding window. If not present, for each pair of stations, the function checks if the route
        between these two stations' hash already exists in the persistence.

        If the route does exist in the db, the function uses the existing route data. If the route does
        not exist, the function uses the transport API client to get the route plan between these
        two stations, writes both that route and the current sub route to persistence.

        This process repeats until the function iterates over all station pairs.

        At the end, it returns the arrival time at the final station as a RouteResponse.
        """
        concurrently = make_awaitable(info)
        persistence = persistence_from_request_context(info)
        transportapi_client = transport_api_client_from_request_context(info)

        _validate_input(user_input)

        station_crs_codes = user_input.route_crs_ids

        departure_times = {}
        current_datetime_of_interest = user_input.datetime_of_interest
        sub_route = [station_crs_codes[0]]
        for i in range(len(station_crs_codes) - 1):
            point_a = station_crs_codes[i]
            point_b = station_crs_codes[i + 1]
            sub_route.append(point_b)

            a_b_hash = generate_hash([point_a, point_b])
            sub_route_hash = generate_hash(sub_route)

            existing_sub_route: Route = await concurrently(
                lambda: persistence.read_route(
                    route_hash=sub_route_hash, datetime_of_interest=user_input.datetime_of_interest
                )
            )

            previous_arrival_time = current_datetime_of_interest

            if existing_sub_route:
                current_datetime_of_interest = existing_sub_route.arrival_at
                departure_times[point_a.name] = existing_sub_route.departure_at
                _check_waiting_time(previous_arrival_time, existing_sub_route.departure_at)
            else:
                existing_a_b_route: Route = await concurrently(
                    lambda: persistence.read_route(
                        route_hash=a_b_hash, datetime_of_interest=current_datetime_of_interest
                    )
                )

                if existing_a_b_route:
                    current_datetime_of_interest = existing_a_b_route.arrival_at
                    departure_times[point_a.name] = existing_a_b_route.departure_at
                    _check_waiting_time(previous_arrival_time, existing_a_b_route.departure_at)
                else:
                    route_plan: TrainRoutePlan = await transportapi_client.get_train_route_plan(
                        point_a.name,
                        point_b.name,
                        datetime_of_interest=current_datetime_of_interest,
                    )

                    _check_waiting_time(previous_arrival_time, route_plan.departure_at)

                    await concurrently(
                        lambda: persistence.write_route(
                            route_hash=a_b_hash,
                            departure_at=route_plan.departure_at,
                            arrival_at=route_plan.arrival_at,
                        )
                    )

                    departure_times[point_a.name] = route_plan.departure_at

                    current_datetime_of_interest = route_plan.arrival_at

                if a_b_hash != sub_route_hash:
                    await concurrently(
                        lambda: persistence.write_route(
                            route_hash=sub_route_hash,
                            departure_at=departure_times[station_crs_codes[0].name],
                            arrival_at=route_plan.arrival_at,
                        )
                    )

        arrival_time = current_datetime_of_interest.strftime(DATETIME_FORMAT)
        return RouteResponse(arrival_time=arrival_time)


def _check_waiting_time(
    arrival_at_current_station: datetime, departure_from_next_station: datetime
) -> None:
    if arrival_at_current_station.astimezone(tz.tzutc()) + timedelta(
        minutes=MAX_WAIT_TIME_IN_MINUTES
    ) < departure_from_next_station.astimezone(tz.tzutc()):
        raise errors.NotThatPatientError(
            f"Max waiting time at a station is {MAX_WAIT_TIME_IN_MINUTES} minutes! "
            f"Wait time too long!"
        )


def _validate_input(user_input: RoutesInput) -> None:
    if len(user_input.route_crs_ids) < 2:
        raise errors.TrainStationCodesLengthError(
            "At minimum two train station codes are required"
        )

    if user_input.datetime_of_interest < datetime.now():
        raise errors.DateTimeInThePastError("Date & Time of interest should be in the future.")

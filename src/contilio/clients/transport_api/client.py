import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

import aiohttp
from aiohttp import ContentTypeError


logger = logging.getLogger(__name__)

TRANSPORT_API_BASE_URL = "https://transportapi.com/v3/uk/public_journey.json"
DEFAULT_TIMEOUT_SECS = 10


@dataclass
class AppCreds:
    app_id: str
    app_key: str


@dataclass
class TrainRoutePlan:
    departure_at: datetime
    arrival_at: datetime

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "TrainRoutePlan":
        return cls(
            departure_at=datetime.fromisoformat(d["routes"][0]["departure_datetime"]),
            arrival_at=datetime.fromisoformat(d["routes"][0]["arrival_datetime"]),
        )


class AsyncHttpClient(Protocol):
    async def get(
        self,
        url: str,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        ...


class AioHttpClient(AsyncHttpClient):  # pragma: no cover
    def __init__(self, default_timeout: Optional[float] = None) -> None:
        self._default_timeout = default_timeout

    async def _fetch(
        self,
        http_verb: str,
        url: str,
        params: Optional[Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        headers = {
            **(headers or {}),
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(
            headers=headers, timeout=aiohttp.ClientTimeout(total=timeout or self._default_timeout)
        ) as session:
            fn = getattr(session, http_verb)
            async with fn(url=url, params=params) as response:
                try:
                    return await response.json()
                except ContentTypeError:
                    logger.debug(
                        f"Received bad response with content-type {response.content_type}: "
                        f"{response.text()}"
                    )
                    raise

    async def get(
        self,
        url: str,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        return await self._fetch(
            http_verb="get", url=url, params=params, headers=headers, timeout=timeout
        )


class TransportApiClientException(Exception):
    pass


class TransportApiClient:
    """
    The transport api http client with a single get journey method.
    """

    def __init__(self, app_creds: AppCreds, http_client: AsyncHttpClient) -> None:
        self._app_creds = app_creds
        self._base_url = TRANSPORT_API_BASE_URL
        self._http_client = http_client

    def _get_params(
        self, point_a: str, point_b: str, datetime_of_interest: datetime
    ) -> Mapping[str, str]:
        return {
            "from": f"crs:{point_a}",
            "to": f"crs:{point_b}",
            "date": datetime_of_interest.strftime("%Y-%m-%d"),
            "time": datetime_of_interest.strftime("%H:%M"),
            "modes": ["train"],
            "app_key": self._app_creds.app_key,
            "app_id": self._app_creds.app_id,
        }

    async def get_train_route_plan(
        self, point_a: str, point_b: str, datetime_of_interest: datetime
    ) -> TrainRoutePlan:
        """
        Hits the transport api base url and supplies the given params as part of the request

        :param point_a: source train station crs 3-letter code
        :param point_b: destination train station crs 3-letter code
        :param datetime_of_interest: date and time after which to look up available plans

        :return: TrainRoutePlan holding departure and arrival times of queried route
        """
        params = self._get_params(point_a, point_b, datetime_of_interest)
        response = await self._http_client.get(url=self._base_url, params=params)
        if not response or "error" in response:
            raise TransportApiClientException(f"Route from {point_a} to {point_b} not found")
        return TrainRoutePlan.from_dict(response)


def create_transportapi_client(app_creds: AppCreds) -> TransportApiClient:
    http_client = AioHttpClient(default_timeout=DEFAULT_TIMEOUT_SECS)
    return TransportApiClient(app_creds=app_creds, http_client=http_client)

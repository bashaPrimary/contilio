from typing import cast
from strawberry.types import Info as GraphQLResolveInfo

from contilio.clients.transport_api.client import (
    TransportApiClient,
    TrainRoutePlan,
    AppCreds,
    create_transportapi_client,
)

__all__ = (
    "TransportApiClient",
    "transport_api_client_from_request_context",
    "TrainRoutePlan",
    "AppCreds",
    "create_transportapi_client",
)


def transport_api_client_from_request_context(
    info: GraphQLResolveInfo,
) -> TransportApiClient:
    if not info.context:
        raise ValueError("Context needs to be present")

    return cast(TransportApiClient, info.context["request"].app.extra["transportapi_client"])

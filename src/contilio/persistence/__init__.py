from typing import cast

from strawberry.types import Info as GraphQLResolveInfo
from contilio.persistence.protocol import Persistence, PersistenceFactory
from contilio.utils.db_connection import init_service, create_engine

__all__ = (
    "init_service",
    "create_engine",
    "persistence_from_request_context",
    "PersistenceFactory",
)


def persistence_from_request_context(info: GraphQLResolveInfo) -> Persistence:
    """A helper function that knows how to retrieve an instance of `Persistence`
    from contextual data assigned to Starlette/FastAPI request.
    """
    if not info.context:
        raise ValueError("Context needs to be present")

    factory = cast(PersistenceFactory, info.context["request"].app.extra["persistence_factory"])
    return factory.create()

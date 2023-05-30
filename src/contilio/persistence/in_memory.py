from datetime import datetime
from typing import (
    List,
    Optional,
    Text,
)

from contilio.persistence.protocol import Route, RouteId, Persistence, PersistenceFactory


def make_graph_persistence_factory() -> PersistenceFactory:
    return InMemoryPersistenceFactory()


class InMemoryPersistenceFactory:
    def __init__(self):
        self.persistence = InMemoryPersistence()

    def create(self) -> Persistence:
        return self.persistence


class InMemoryPersistence(Persistence):
    def __init__(self):
        self.id: int = 0
        self.routes_table: List[Route] = []

    def read_route(self, route_hash: Text, datetime_of_interest: datetime) -> Optional[Route]:
        try:
            return next(
                iter(
                    [
                        r
                        for r in self.routes_table
                        if r.hashed == route_hash and r.departure_at >= datetime_of_interest
                    ]
                )
            )
        except StopIteration:
            return None

    def write_route(
        self, route_hash: Text, departure_at: datetime, arrival_at: datetime
    ) -> RouteId:
        route_id = self.id
        self.routes_table.append(
            Route(id=route_id, hashed=route_hash, departure_at=departure_at, arrival_at=arrival_at)
        )
        self.id += 1
        return route_id

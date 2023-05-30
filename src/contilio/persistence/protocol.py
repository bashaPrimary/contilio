from dataclasses import dataclass
from datetime import datetime
from typing import Text, Optional
from typing_extensions import Protocol

RouteId = int


@dataclass(frozen=True)
class Route:
    id: RouteId
    hashed: Text
    departure_at: datetime
    arrival_at: datetime


class Persistence(Protocol):
    def read_route(self, route_hash: Text, datetime_of_interest: datetime) -> Optional[Route]:
        ...

    def write_route(
        self, route_hash: Text, departure_at: datetime, arrival_at: datetime
    ) -> RouteId:
        ...


class PersistenceFactory(Protocol):
    def create(self) -> Persistence:
        ...

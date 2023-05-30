import datetime
from typing import List, Text, Any, cast, Optional

from sqlalchemy import and_
from sqlalchemy.engine import Engine, Row
from sqlalchemy.sql import expression as sql

from logging import getLogger
from contilio.journey_planner.model import Route
from contilio.persistence.protocol import Route as DomainRoute, RouteId

from contilio.persistence.protocol import PersistenceFactory, Persistence

logger = getLogger(__name__)


class JourneyPlannerPersistenceFactory(PersistenceFactory):
    def __init__(self, engine: Engine):
        self._engine = engine

    def create(self) -> Persistence:
        return JourneyPlannerPersistence(self._engine)


class JourneyPlannerPersistence(Persistence):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.route_table = Route.__table__

    @staticmethod
    def _parse_route_row(row: Row) -> DomainRoute:
        (route_id, hashed, departure_at, arrival_at) = row

        route = DomainRoute(
            id=route_id, hashed=hashed, departure_at=departure_at, arrival_at=arrival_at
        )

        return route

    def read_route(self, route_hash: Text, datetime_of_interest: datetime) -> Optional[Route]:
        rows = self._execute(
            sql.select(self.route_table).where(
                and_(
                    self.route_table.c.hashed == route_hash,
                    self.route_table.c.departure_at >= datetime_of_interest,
                )
            )
        )

        if rows:
            return self._parse_route_row(rows[0])
        return None

    def write_route(
        self, route_hash: Text, departure_at: datetime, arrival_at: datetime
    ) -> RouteId:
        result = self._execute(
            sql.insert(self.route_table)
            .values(hashed=route_hash, departure_at=departure_at, arrival_at=arrival_at)
            .returning(self.route_table.c.id)
        )

        (route_id,) = next(iter(result))

        return cast(int, route_id)

    def _execute(self, expr: Any) -> List[Row]:
        """Produces a list with results of the query invocation.

        To actually run the ``expr``, the calling side needs to materialize the generated
        values in any form. The query runs only when at least one result row is requested.
        Hence, lazy resource management is achieved here.
        """

        with self.engine.connect() as conn:
            result = conn.execution_options(
                stream_results=expr.is_selectable, isolation_level="AUTOCOMMIT"
            ).execute(expr)

            return [row for row in result]

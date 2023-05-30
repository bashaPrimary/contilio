from typing import List
from datetime import datetime

import strawberry

from contilio.domain.enums import UKTrainStationCode


@strawberry.input
class RoutesInput:
    route_crs_ids: List[UKTrainStationCode] = strawberry.field(
        description="Unique 3 letter code UK train station crs identifiers defining the route"
    )
    datetime_of_interest: datetime = strawberry.field(
        description="Starting date and time to look for departures given a specific route."
    )

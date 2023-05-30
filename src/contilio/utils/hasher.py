import hashlib
from typing import List, Text

from contilio.domain.enums import UKTrainStationCode


def generate_hash(route: List[UKTrainStationCode]) -> Text:
    """
    Uses sha256 hashing algorithm to encode a given route

    :param route: a given list of train station crs codes
    :return: a hash of the route
    """
    route_string = ",".join([r.name for r in route])
    return hashlib.sha256(route_string.encode()).hexdigest()

import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

ROUTE_HASH_LEN = 256


class Route(Base):  # type: ignore
    """
    A route consists of 2 of more journey points, the entire route is hashed.

    This table stores:
        id: the id of the route
        hash: hash of entire route from source to destination
        departure_at: date and time leaving source
        arrival_at: date and time arriving at destination
    """

    __tablename__ = "route"

    id = sqla.Column(sqla.Integer, primary_key=True, autoincrement=True)
    hashed = sqla.Column(sqla.String(ROUTE_HASH_LEN), nullable=False)
    departure_at = sqla.Column(sqla.DateTime, nullable=False)
    arrival_at = sqla.Column(sqla.DateTime, nullable=False)

    __table_args__ = (sqla.Index("idx_hashed_departure_at", "hashed", "departure_at"),)

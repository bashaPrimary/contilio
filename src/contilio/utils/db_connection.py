import logging
from pathlib import Path
from typing import Text

import sqlalchemy as sqla
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import declarative_base
from contilio.config import RequiredEnviron

logger = logging.getLogger(__name__)

Base = declarative_base()


def root(alembic_directory) -> Text:
    return f"{str(Path(__file__).parent.parent)}/{alembic_directory}"


def init_service(
    env: RequiredEnviron,
    use_alembic: bool,
) -> sqla.engine.Engine:
    """Init all necessary DB and meta stuff for the service"""
    engine = create_engine(env)
    alembic_directory = env.ALEMBIC_DIRECTORY
    if use_alembic:
        alembic_cfg_path = f"{root(alembic_directory)}/alembic.ini"
        command.upgrade(Config(alembic_cfg_path), "heads")
    else:
        Base.metadata.create_all(engine)
    return engine


def create_engine(
    env: RequiredEnviron,
) -> sqla.engine.Engine:
    return sqla.create_engine(
        f"sqlite:///{root(env.ALEMBIC_DIRECTORY)}/{env.JP_SQLLITE_DB_FILE_NAME}"
    )

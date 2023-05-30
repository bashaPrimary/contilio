import os

from logging import getLogger, INFO

import dotenv

import uvicorn
from contilio import persistence
from contilio.application import init_app
from contilio.cli import arg_parser
from contilio.config import RequiredEnviron

logger = getLogger(__name__)


def main(
    env: RequiredEnviron,
    initialise_journey_planner_db: bool = True,
) -> None:
    if initialise_journey_planner_db:
        logger.info("Initialising Journey Planner database...")
        persistence.init_service(env, env.JP_RUN_ALEMBIC_MIGRATIONS)
    uvicorn.run(
        "contilio.__main__:app",
        host="0.0.0.0",
        port=env.SERVICE_PORT,
        workers=env.NUM_UVICORN_WORKERS,
        log_level=INFO,
    )


if __name__ == "__main__":
    """Entry-point to our service"""
    dotenv.load_dotenv()
    env = RequiredEnviron.parse_obj(os.environ)
    args = arg_parser().parse_args()
    logger.info("Got CLI arguments: %s", dict(args._get_kwargs()))
    main(env=env, initialise_journey_planner_db=args.initialise_journey_planner_db)
else:
    app = init_app()

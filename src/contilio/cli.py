from argparse import ArgumentParser

from contilio.config import SERVICE_NAME


def arg_parser() -> ArgumentParser:
    parser = ArgumentParser(SERVICE_NAME, description=f"Runs the {SERVICE_NAME} API")
    parser.add_argument("--initialise-journey-planner-db", action="store_true")
    return parser

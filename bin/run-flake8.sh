#!/usr/bin/env bash
poetry run flake8 --config ./setup.cfg src --exclude src/contilio/journey_planner/migrations

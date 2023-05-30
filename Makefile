.PHONY: install \
        tests \
		lint \
		run

install:
	poetry install

lint:
	bin/run-black.sh && \
    bin/run-flake8.sh
	
tests:
	poetry run pytest

export YELLOW := \033[1;33m
export NO_COLOUR := \033[0m

_echo_minimal:
	@echo "${YELLOW}Running Contilio Train Journey Planner."
	@echo
	@echo "This make step is intended for local development on a graphQL endpoint."
	@echo "You can view it at http://localhost:5002/graphql"
	@echo "${NO_COLOUR}"

run: install _echo_minimal
	poetry run python -m contilio --initialise-journey-planner-db
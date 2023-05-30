FROM python:3.10-slim-buster as os-base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

FROM os-base as poetry-base

RUN pip3 install poetry
ENV PATH="/root/.poetry/bin:$PATH"
RUN poetry config virtualenvs.create false

FROM poetry-base as app-base

ARG APPDIR=/app
WORKDIR $APPDIR/
COPY src ./src
COPY pyproject.toml ./pyproject.toml
RUN poetry install --no-dev

FROM app-base as main

EXPOSE 5002

CMD ["python", "src/contilio/__main__.py"]
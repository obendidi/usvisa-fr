FROM python:3.10-slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # for installing poetry
    curl \
    # for installing git deps
    git \
    # for building python deps
    build-essential

# make poetry install to this location
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

# install poetry
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /usvisa-fr

COPY pyproject.toml /usvisa-fr/pyproject.toml
COPY poetry.lock /usvisa-fr/poetry.lock

RUN poetry install --no-root --no-dev

COPY usvisa_fr /usvisa-fr/usvisa_fr

RUN poetry install --no-dev

ENTRYPOINT [ "poetry", "run", "python" ]
CMD [ "usvisa_fr/main.py" ]

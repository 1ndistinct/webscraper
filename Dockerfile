FROM python:3.12-slim-bookworm AS requirements
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN apt update &&  uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS production
WORKDIR /app
RUN groupadd app && useradd -g app --home-dir /app --create-home app
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=requirements /app/.venv /app/.venv
COPY ./webscraper ./webscraper
RUN chown -R app /app && chmod -R 700 /app
USER app
ENTRYPOINT [ "python","-m","webscraper" ]
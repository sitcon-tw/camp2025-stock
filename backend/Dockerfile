FROM ghcr.io/astral-sh/uv:python3.13-alpine

ADD . /app
WORKDIR /app
RUN uv sync --locked

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["uv", "run", "uvicorn", "--host", "0.0.0.0", "app.main_refactored:app"]

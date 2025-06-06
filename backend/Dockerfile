FROM ghcr.io/astral-sh/uv:python3.13-alpine

ADD . /app
WORKDIR /app
RUN uv sync --locked

ENV PORT=8080
EXPOSE 8080

WORKDIR /app/app

ENTRYPOINT ["uv", "run", "main.py"]

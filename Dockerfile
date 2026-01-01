FROM python:3.13-slim AS builder

ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_NO_MANAGED_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT=/venv \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/venv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv $VIRTUAL_ENV && \
    uv sync --no-install-project --no-dev --no-editable

COPY src/ /app/

FROM python:3.13-slim

ARG PORT=8000

ENV PATH="/venv/bin:$PATH" \
    PORT=${PORT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PYTHONPATH="/app"

WORKDIR /app
EXPOSE ${PORT}

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        smartmontools \
        zfsutils-linux \
        bash && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --link --from=builder /venv /venv
COPY --link --from=builder /app /app

RUN echo "source /venv/bin/activate" >> /root/.bashrc

CMD ["/app/run.sh"]
# syntax=docker/dockerfile:1.7

FROM python:3.14-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/var/cache/uv \
    HF_HOME=/var/cache/resume-analyzer/huggingface \
    TRANSFORMERS_CACHE=/var/cache/resume-analyzer/huggingface/transformers \
    TORCH_HOME=/var/cache/resume-analyzer/torch \
    XDG_CACHE_HOME=/var/cache/resume-analyzer

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      curl \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv

COPY backend/pyproject.toml backend/uv.lock ./

RUN --mount=type=cache,target=/var/cache/uv \
    uv sync --frozen --no-dev

COPY backend/ ./

RUN mkdir -p /var/lib/resume-analyzer/uploads \
    /var/log/resume-analyzer \
    /var/cache/resume-analyzer/huggingface \
    /var/cache/resume-analyzer/torch

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "main:server", "--host", "0.0.0.0", "--port", "8000"]

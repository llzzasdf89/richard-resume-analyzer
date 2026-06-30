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


FROM node:20-bookworm-slim AS frontend-builder

ARG VITE_API_BASE_URL=/api
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_SUPABASE_URL=${VITE_SUPABASE_URL} \
    VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY frontend/ ./

RUN npm run build


FROM nginx:1.27-alpine AS frontend

RUN printf '%s\n' \
    'server {' \
    '    listen 80;' \
    '    server_name _;' \
    '    root /usr/share/nginx/html;' \
    '    index index.html;' \
    '    client_max_body_size 5m;' \
    '    location /api/ {' \
    '        proxy_pass http://backend:8000;' \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '        proxy_buffering off;' \
    '    }' \
    '    location / {' \
    '        try_files $uri $uri/ /index.html;' \
    '    }' \
    '}' \
    > /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

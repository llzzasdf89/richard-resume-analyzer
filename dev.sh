#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

require_command() {
  local command_name="$1"

  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}"
    echo "Please install ${command_name} and run this script again."
    exit 1
  fi
}

ensure_backend_dependencies() {
  require_command uv

  echo "Checking backend dependencies..."

  if [[ ! -d "${ROOT_DIR}/backend/.venv" ]]; then
    echo "Backend virtual environment not found. Installing dependencies..."
    (
      cd "${ROOT_DIR}/backend"
      UV_CACHE_DIR=.uv-cache uv sync
    )
    return
  fi

  if ! (
    cd "${ROOT_DIR}/backend"
    UV_CACHE_DIR=.uv-cache uv run --no-sync python -c "import fastapi, uvicorn" >/dev/null 2>&1
  ); then
    echo "Backend dependencies are incomplete. Installing dependencies..."
    (
      cd "${ROOT_DIR}/backend"
      UV_CACHE_DIR=.uv-cache uv sync
    )
    return
  fi

  echo "Backend dependencies are ready."
}

ensure_frontend_dependencies() {
  require_command npm

  echo "Checking frontend dependencies..."

  if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]] || [[ ! -x "${ROOT_DIR}/frontend/node_modules/.bin/vite" ]]; then
    echo "Frontend dependencies not found. Installing dependencies..."
    (
      cd "${ROOT_DIR}/frontend"
      npm install
    )
    return
  fi

  if [[ -f "${ROOT_DIR}/frontend/package-lock.json" ]] && [[ -f "${ROOT_DIR}/frontend/node_modules/.package-lock.json" ]] && [[ "${ROOT_DIR}/frontend/package-lock.json" -nt "${ROOT_DIR}/frontend/node_modules/.package-lock.json" ]]; then
    echo "Frontend lockfile is newer than installed dependencies. Installing dependencies..."
    (
      cd "${ROOT_DIR}/frontend"
      npm install
    )
    return
  fi

  echo "Frontend dependencies are ready."
}

cleanup() {
  echo
  echo "Stopping development servers..."

  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

ensure_backend_dependencies
ensure_frontend_dependencies

echo "Starting backend at http://127.0.0.1:8000"
(
  cd "${ROOT_DIR}/backend"
  UV_CACHE_DIR=.uv-cache uv run uvicorn main:server --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend at http://127.0.0.1:5173"
(
  cd "${ROOT_DIR}/frontend"
  npm run dev -- --host 127.0.0.1 --port 5173
) &
FRONTEND_PID=$!

echo
echo "Development servers are starting:"
echo "- Backend:  http://127.0.0.1:8000"
echo "- Frontend: http://127.0.0.1:5173"
echo
echo "Press Ctrl+C to stop both servers."

wait "${BACKEND_PID}" "${FRONTEND_PID}"

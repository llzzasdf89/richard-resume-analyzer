import json
import time

from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import logger


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

        user = getattr(request.state, "user", None)
        request_id = getattr(request.state, "request_id", None)
        payload = {
            "event": "http_request",
            "request_id": request_id,
            "user_id": user.get("id") if isinstance(user, dict) else None,
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        logger.info(json.dumps(payload, ensure_ascii=False))
        return response

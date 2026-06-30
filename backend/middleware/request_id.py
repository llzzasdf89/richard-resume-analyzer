from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_HEADER = "X-Request-ID"


def resolve_request_id(request: Request) -> str:
    existing = request.headers.get(REQUEST_ID_HEADER)
    return existing if existing else f"req_{uuid4().hex}"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = resolve_request_id(request)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

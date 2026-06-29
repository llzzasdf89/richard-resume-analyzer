from starlette.requests import Request

from middleware.request_id import REQUEST_ID_HEADER, resolve_request_id


def test_uses_existing_request_id_from_header():
    scope = {
        "type": "http",
        "headers": [(REQUEST_ID_HEADER.lower().encode(), b"req_123")],
    }
    request = Request(scope)

    assert resolve_request_id(request) == "req_123"


def test_generates_request_id_when_missing():
    scope = {"type": "http", "headers": []}
    request = Request(scope)

    assert resolve_request_id(request).startswith("req_")

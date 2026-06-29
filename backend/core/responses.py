from typing import Any


def api_success(data: Any = None, message: str = "OK") -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "code": 200,
    }


def api_error(message: str, data: Any = None) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": data,
        "code": 500,
    }

from core.responses import api_error, api_success


def test_api_success_uses_standard_shape():
    assert api_success({"id": "123"}) == {
        "success": True,
        "message": "OK",
        "data": {"id": "123"},
        "code": 200,
    }


def test_api_error_uses_standard_shape_and_business_code_500():
    assert api_error("Failed") == {
        "success": False,
        "message": "Failed",
        "data": None,
        "code": 500,
    }

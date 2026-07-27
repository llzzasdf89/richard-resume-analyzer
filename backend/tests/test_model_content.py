import pytest

from model_content import extract_json_object, extract_model_text


def test_extract_model_text_ignores_thinking_and_keeps_visible_array_content():
    content = [
        "",
        {
            "type": "thinking",
            "thinking": "Return the requested JSON.",
            "index": 0,
            "signature": "",
        },
        '{"requirements":"Build web products","must_skills":["HTML"],"nice_skills":[]}',
    ]

    assert extract_model_text(content) == (
        '{"requirements":"Build web products",'
        '"must_skills":["HTML"],"nice_skills":[]}'
    )


def test_extract_model_text_supports_text_blocks():
    content = [
        {"type": "thinking", "thinking": "Internal reasoning"},
        {"type": "text", "text": "Visible answer"},
    ]

    assert extract_model_text(content) == "Visible answer"


def test_extract_json_object_accepts_markdown_fenced_json():
    content = """Result:
```json
{"agents":["expression"]}
```"""

    assert extract_json_object(content) == {"agents": ["expression"]}


def test_extract_json_object_accepts_direct_object_content():
    content = {
        "requirements": "Build web products",
        "must_skills": ["HTML"],
        "nice_skills": [],
    }

    assert extract_json_object(content) == {
        "requirements": "Build web products",
        "must_skills": ["HTML"],
        "nice_skills": [],
    }


def test_extract_json_object_rejects_content_without_an_object():
    with pytest.raises(ValueError, match="JSON object"):
        extract_json_object(["", {"type": "thinking", "thinking": "No answer"}])

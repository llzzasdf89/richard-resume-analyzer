import json
from typing import Any


_VISIBLE_TEXT_BLOCK_TYPES = {"text", "output_text"}


def extract_model_text(content: Any) -> str:
    """Return user-visible text from either legacy strings or content blocks."""
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif (
            isinstance(block, dict)
            and block.get("type") in _VISIBLE_TEXT_BLOCK_TYPES
            and isinstance(block.get("text"), str)
        ):
            parts.append(block["text"])
    return "".join(parts)


def extract_json_object(content: Any) -> dict[str, Any]:
    """Extract the first valid JSON object from visible model output."""
    if isinstance(content, dict):
        return content

    text = extract_model_text(content)
    decoder = json.JSONDecoder()

    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value

    raise ValueError("Model response did not contain a valid JSON object")

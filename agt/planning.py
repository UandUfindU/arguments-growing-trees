"""Parse transport output without confusing schema conformance with proxy validity."""
import json
import re

from .proxy import RELATIONS


def parse_plan(content: str, phase: str, context: dict) -> dict:
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    result = json.loads(clean)
    if not isinstance(result, dict):
        raise ValueError("Plan must be an object")
    if phase == "attach":
        parent = context.get("tree", {}).get("nodes", {}).get(result.get("parent_id"), {})
        if parent.get("kind") != "claim":
            raise ValueError("parent_id must identify an existing claim, not evidence")
        if not isinstance(result.get("claim"), str) or not result["claim"].strip():
            raise ValueError("Attachment needs a scoped claim")
        specs = [result]
    else:
        tests, claims = result.get("tests"), result.get("claims", [])
        if not isinstance(tests, list) or not isinstance(claims, list):
            raise ValueError("tests and claims must be arrays")
        if phase == "verify" and not tests:
            if not isinstance(result.get("reason"), str) or not result["reason"].strip():
                raise ValueError("Empty verification tests need a reason")
        for spec in tests:
            if not isinstance(spec, dict) or not isinstance(spec.get("plan"), dict):
                raise ValueError("Each test needs a plan object")
            for key in ("null", "alternative"):
                if not isinstance(spec["plan"].get(key), str) or not spec["plan"][key].strip():
                    raise ValueError(f"Test requires nonempty string {key}")
        specs = claims + tests
    for spec in specs:
        if not isinstance(spec, dict) or spec.get("relation", "context") not in RELATIONS:
            raise ValueError("relation must be supports, challenges, or context")
    return result

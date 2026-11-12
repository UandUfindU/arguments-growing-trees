"""Small validation boundary between model proposals and registered CPU tools."""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .tree import timestamp

HYPOTHESES = {
    "pearson": {
        "null": "Zero linear correlation between quarter index and revenue",
        "alternative": "Two-sided nonzero linear correlation between quarter index and revenue",
        "alternative_code": "two-sided"},
    "chi_square": {
        "null": "Period and pathway are independent",
        "alternative": "Association between period and pathway",
        "alternative_code": "association"},
}

RELATIONS = {"supports", "challenges", "context"}


def read_registered_rows(dataset: dict, cutoff: str) -> tuple[bytes, list[dict]]:
    if timestamp(dataset["available_at"]) > timestamp(cutoff):
        raise ValueError("Dataset unavailable at cutoff; choose an earlier registered source")
    raw = Path(dataset["path"]).read_bytes()
    reader = csv.DictReader(raw.decode("utf-8-sig").splitlines(),
                            delimiter=dataset.get("delimiter", ","))
    columns = list(dataset["columns"])
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("Missing or duplicate CSV headers")
    if not set(columns).issubset(reader.fieldnames):
        raise ValueError("Registered schema columns absent from actual data")
    rows = list(reader)
    if not rows:
        raise ValueError("Empty registered data")
    for row in rows:
        for column, dtype in dataset["column_types"].items():
            value = row.get(column)
            if value is None or not value.strip():
                raise ValueError(f"Missing value in {column}")
            if dtype == "number":
                try:
                    valid = math.isfinite(float(value))
                except ValueError:
                    valid = False
                if not valid:
                    raise ValueError(f"Nonfinite or nonnumeric value in {column}")
    keys = dataset["observation_key"]
    identities = [tuple(row[k] for k in keys) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate observation keys; resolve overlapping observations first")
    return raw, rows


def validate_method(plan: dict, dataset: dict):
    method = plan.get("operation")
    if method not in dataset["operations"]:
        raise ValueError("Method not registered for dataset")
    expected = dataset["suggested_test"]
    if any(plan.get(key) != value for key, value in expected.items()):
        raise ValueError("Column mapping differs from registered test; review catalog")
    for name in ("null", "alternative"):
        if not isinstance(plan.get(name), str) or not plan[name].strip():
            raise ValueError(f"Missing statistical hypothesis: {name}")
    # The registry owns H0/H1. Prose heuristics cannot validate an arbitrary
    # model-supplied statistical hypothesis against an executor.
    if any(plan.get(key) != value for key, value in HYPOTHESES[method].items()):
        raise ValueError(f"{method} H0/H1/direction must match registered hypotheses")


def validate_proxy_spec(spec: dict, dataset: dict):
    plan = spec["plan"]
    validate_method(plan, dataset)
    proxy = plan.get("proxy", {})
    for key in ("target_claim_id", "quantity", "entity", "period", "unit",
                "interpretation", "limitations", "available_at", "sample_requirements", "statistical_assumptions"):
        if not isinstance(proxy.get(key), str) or not proxy[key].strip():
            raise ValueError(f"Proxy specification missing {key}")
    for key in ("quantity", "entity", "period", "unit", "available_at",
                "sample_requirements", "statistical_assumptions"):
        if proxy[key] != dataset[key]:
            raise ValueError(f"Proxy {key} must match registered scope exactly")
    if proxy["target_claim_id"] != spec["parent"]:
        raise ValueError("Proxy target must equal test parent")
    if spec.get("relation") not in RELATIONS or not spec.get("rationale", "").strip():
        raise ValueError("Each proxy edge needs a relation and concrete rationale")


def validate_coverage(coverage: dict):
    if not isinstance(coverage, dict):
        raise ValueError("Missing explicit operationalization coverage")
    if not isinstance(coverage.get("operationalized"), str) or not coverage["operationalized"].strip():
        raise ValueError("State what the registered data actually operationalize")
    unresolved = coverage.get("unresolved")
    if not isinstance(unresolved, list) or any(not isinstance(x, str) or not x.strip() for x in unresolved):
        raise ValueError("coverage.unresolved must list missing aspects")
    if not isinstance(coverage.get("full_hypothesis_covered"), bool):
        raise ValueError("Declare whether the original hypothesis is fully covered")
    if unresolved and coverage["full_hypothesis_covered"]:
        raise ValueError("Unresolved aspects cannot count as full hypothesis coverage")

"""Allowlisted CPU tests. LLM output is a plan, never executable Python."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

import numpy as np
from scipy import stats

from .proxy import read_registered_rows, validate_method


@dataclass(frozen=True)
class TestOutcome:
    statistic: float
    p_value: float
    sample_size: float
    assumptions: dict
    extra: dict = field(default_factory=dict)


def contingency_test(plan: dict, rows: list[dict]) -> TestOutcome:
    r, c, v = plan["row"], plan["column"], plan["value"]
    ri = sorted({x[r] for x in rows})
    ci = sorted({x[c] for x in rows})
    cells = [(row[r], row[c]) for row in rows]
    if len(cells) != len(set(cells)):
        raise ValueError("Duplicate contingency cells")
    table = np.zeros((len(ri), len(ci)))
    for x in rows:
        number = float(x[v])
        if not math.isfinite(number) or number < 0 or not number.is_integer():
            raise ValueError("Contingency counts must be nonnegative integers")
        table[ri.index(x[r]), ci.index(x[c])] += number
    if min(table.shape) < 2:
        raise ValueError("Need at least a 2x2 table")
    if table.sum() <= 0 or (table.sum(axis=0) == 0).any() or (table.sum(axis=1) == 0).any():
        raise ValueError("Empty contingency margins")
    statistic, p, dof, expected = stats.chi2_contingency(table)
    if expected.min() < 5:
        raise ValueError("Insufficient expected counts for registered asymptotic chi-square test (need >=5)")
    assumptions = {"minimum_expected_count": float(expected.min()),
                   "independence_of_observations": "requires_domain_review"}
    n = float(table.sum())
    effect = math.sqrt(float(statistic) / (n * (min(table.shape) - 1)))
    extra = {"dof": int(dof), "cramers_v": effect}
    return TestOutcome(float(statistic), float(p), n, assumptions, extra)


def correlation_test(plan: dict, rows: list[dict]) -> TestOutcome:
    x = np.array([float(r[plan["x"]]) for r in rows])
    y = np.array([float(r[plan["y"]]) for r in rows])
    if len(x) < 4 or not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError("Need >=4 finite paired observations")
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        raise ValueError("Constant series cannot identify correlation")
    statistic, p = stats.pearsonr(x, y, alternative="two-sided")
    if not (math.isfinite(statistic) and math.isfinite(p)):
        raise ValueError("Undefined test")
    n = len(x)
    assumptions = {"independent_bivariate_normal_observations": "requires_domain_review",
                   "time_series_dependence": "not_corrected"}
    return TestOutcome(float(statistic), float(p), n, assumptions)


def execute_test(plan: dict, datasets: dict, as_of: str) -> dict:
    dataset = datasets[plan["dataset_id"]]
    validate_method(plan, dataset)
    raw, rows = read_registered_rows(dataset, as_of)
    operation = plan["operation"]
    executor = {"chi_square": contingency_test, "pearson": correlation_test}[operation]
    outcome = executor(plan, rows)
    p = outcome.p_value
    p = float(p)
    if not 0 < p <= 1:
        raise ValueError("Underflowed or invalid p-value; no clipped formal evidence")
    # POPPER's fixed kappa=0.5 p-to-e calibrator. This is not P(hypothesis=true).
    log_e = math.log(0.5) - 0.5 * math.log(p)
    return {"p_value": p, "e_value": math.exp(log_e), "log_e": log_e,
            "statistic": outcome.statistic, "sample_size": outcome.sample_size, **outcome.extra,
            "null": plan["null"], "alternative": plan["alternative"],
            "alternative_code": plan["alternative_code"],
            "proxy_scope": {key: dataset[key] for key in ("quantity", "entity", "period", "unit")},
            "semantic_review": {"status": "requires_domain_review",
                "registered_scope_checked": True,
                "parent_entailment_established": False,
                "note": "Execution tests the registered sample hypothesis, not the parent investment conclusion."},
            "evidence_direction": "undetermined_requires_review",
            "operation": operation, "dataset_id": plan["dataset_id"],
            "data_sha256": hashlib.sha256(raw).hexdigest(),
            "data_family": dataset.get("data_family", plan["dataset_id"]),
            "available_at": dataset["available_at"], "as_of": as_of,
            "source_url": dataset["source_url"],
            "calibrator": {"name": "power_p_to_e", "kappa": 0.5},
            "assumptions": outcome.assumptions, "validity_status": "requires_review",
            "root_aggregation": "not_established",
            "execution": "scipy_cpu_allowlisted"}

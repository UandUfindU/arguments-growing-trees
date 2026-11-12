"""Allowlisted CPU tests. LLM output is a plan, never executable Python."""
from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import numpy as np
from scipy import stats


def execute_test(plan: dict, datasets: dict, as_of: str) -> dict:
    dataset = datasets[plan["dataset_id"]]
    if dataset["available_at"] > as_of:
        raise ValueError("Dataset not available at replay cutoff")
    path = Path(dataset["path"])
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines(),
                               delimiter=dataset.get("delimiter", ",")))
    operation = plan["operation"]
    if operation == "chi_square":
        r, c, v = plan["row"], plan["column"], plan["value"]
        ri = sorted({x[r] for x in rows})
        ci = sorted({x[c] for x in rows})
        table = np.zeros((len(ri), len(ci)))
        for x in rows:
            number = float(x[v])
            if number < 0 or not number.is_integer():
                raise ValueError("Contingency counts must be nonnegative integers")
            table[ri.index(x[r]), ci.index(x[c])] += number
        if min(table.shape) < 2:
            raise ValueError("Need at least a 2x2 table")
        statistic, p, dof, expected = stats.chi2_contingency(table)
        assumptions = {"minimum_expected_count": float(expected.min()),
                       "independence_of_observations": "requires_domain_review"}
        n = float(table.sum())
        effect = math.sqrt(float(statistic) / (n * (min(table.shape) - 1)))
        extra = {"dof": int(dof), "cramers_v": effect}
    elif operation == "pearson":
        x = np.array([float(r[plan["x"]]) for r in rows])
        y = np.array([float(r[plan["y"]]) for r in rows])
        if len(x) < 4 or not (np.isfinite(x).all() and np.isfinite(y).all()):
            raise ValueError("Need >=4 finite paired observations")
        statistic, p = stats.pearsonr(x, y)
        if not (math.isfinite(statistic) and math.isfinite(p)):
            raise ValueError("Undefined test")
        n = len(x)
        assumptions = {"independent_bivariate_normal_observations": "requires_domain_review",
                       "time_series_dependence": "not_corrected"}
        extra = {}
    else:
        raise ValueError("Unsupported test; allowed: chi_square, pearson")
    p = float(p)
    if not 0 < p <= 1:
        raise ValueError("Underflowed or invalid p-value; no clipped formal evidence")
    # POPPER's fixed kappa=0.5 p-to-e calibrator. This is not P(hypothesis=true).
    log_e = math.log(0.5) - 0.5 * math.log(p)
    return {"p_value": p, "e_value": math.exp(log_e), "log_e": log_e,
            "statistic": float(statistic), "sample_size": n, **extra,
            "null": plan["null"], "alternative": plan["alternative"],
            "operation": operation, "dataset_id": plan["dataset_id"],
            "data_sha256": hashlib.sha256(raw).hexdigest(),
            "available_at": dataset["available_at"], "as_of": as_of,
            "source_url": dataset["source_url"],
            "calibrator": {"name": "power_p_to_e", "kappa": 0.5},
            "assumptions": assumptions, "validity_status": "requires_review",
            "root_aggregation": "not_established",
            "execution": "scipy_cpu_allowlisted"}

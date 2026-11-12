"""Joint affected-path masking and an explicitly untrained inference adapter."""
from __future__ import annotations

import copy
import json
import math

from .tree import affected_paths


def masked_example(snapshot: dict, attachments: list[str], labels: dict | None = None) -> dict:
    """Input must be a point-in-time snapshot; labels are supplied separately.

    Drop the whole numeric/decision payload on affected nodes. Event logs may
    contain ancestors' numbers, so exclude logs from model input altogether.
    The same transform is used at training and inference.
    """
    tree = copy.deepcopy(snapshot)
    affected = affected_paths(tree, attachments)
    tree.pop("events", None)
    for node_id, node in tree["nodes"].items():
        node.pop("prediction", None)
        if node_id in affected:
            node["result"] = {"masked": True}
            # Prose on a target may quote its measured e/p. Keep the structure
            # and test design, but isolate declared numeric execution payloads.
    supplied = labels or {}
    targets = {}
    for node_id in affected:
        record = supplied.get(node_id)
        if record is not None:
            if record.get("execution") != "scipy_cpu_allowlisted":
                raise ValueError("Labels must come from recorded executions")
            value = float(record["log_e"])
            if not math.isfinite(value):
                raise ValueError("Nonfinite target")
            targets[node_id] = value
    return {"tree": tree, "target_ids": affected, "labels": targets,
            "supervision": "observed_execution_only"}


def model_text(example: dict) -> str:
    return json.dumps({"tree": example["tree"], "target_ids": example["target_ids"]},
                      ensure_ascii=False, sort_keys=True)


class UntrainedSystem1:
    status = "untrained"

    def predict(self, snapshot: dict, attachments: list[str]) -> dict:
        example = masked_example(snapshot, attachments)
        return {"status": self.status, "model_revision": None,
                "input_revision": snapshot["revision"],
                "target_ids": example["target_ids"],
                "log_e": {k: None for k in example["target_ids"]},
                "masked_input": example}

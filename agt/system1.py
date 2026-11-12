"""Claim-conditioned LOCAL scalar prediction; path masking is anti-leakage only."""
from __future__ import annotations
import copy
import json
import math
from .tree import affected_paths


def masked_example(snapshot, attachments, labels=None, *, news=None, target_claim=None):
    if len(attachments) != 1:
        raise ValueError("Exactly one local target required")
    local = attachments[0]
    tree = copy.deepcopy(snapshot)
    affected = set(affected_paths(tree, attachments))
    records = [tree["nodes"][k].get("result") or {} for k in affected]
    hashes = {r.get("data_sha256") for r in records} - {None}
    families = {r.get("data_family") for r in records} - {None}
    urls = {r.get("source_url") for r in records} - {None}
    sources = {json.dumps(tree["nodes"][k].get("source") or {}, sort_keys=True) for k in affected}
    sources.discard("{}")
    duplicates = {k for k,n in tree["nodes"].items() if
        (n.get("result") or {}).get("data_sha256") in hashes or
        (n.get("result") or {}).get("data_family") in families or
        (n.get("result") or {}).get("source_url") in urls or
        json.dumps(n.get("source") or {}, sort_keys=True) in sources}
    masked = affected | duplicates
    # Duplicate-data ancestors can contain cumulative copies of the target.
    masked |= set(affected_paths(tree, list(duplicates)))
    tree.pop("events", None)
    for k,n in tree["nodes"].items():
        n.pop("prediction", None)
        n.pop("local_slot", None)
        n.pop("aggregation", None)
        n.pop("cumulative", None)
        if k in masked:
            n["result"] = {"masked": True}
    supplied = labels or {}
    if set(supplied) - {local}:
        raise ValueError("Ancestor/path regression targets forbidden")
    targets = {}
    if local in supplied:
        r = supplied[local]
        if r.get("execution") != "scipy_cpu_allowlisted" or not math.isfinite(float(r["log_e"])):
            raise ValueError("Finite executed local label required")
        targets[local] = float(r["log_e"])
    return {"tree": tree, "local_target_id": local, "target_ids": [local],
            "mask_ids": sorted(masked), "auxiliary_mask_ids": sorted(masked-affected),
            "news": copy.deepcopy(news), "target_claim": copy.deepcopy(target_claim),
            "labels": targets, "supervision": "observed_execution_only"}


def model_text(example):
    return json.dumps({k:example[k] for k in ("tree", "local_target_id", "news", "target_claim")}, ensure_ascii=False, sort_keys=True)


class UntrainedSystem1:
    status = "untrained"
    def predict(self, snapshot, attachments):
        local = attachments[0]
        node = snapshot["nodes"][local]
        news = next((n["source"] for n in snapshot["nodes"].values() if n["parent"] == local and n["kind"] == "textual_evidence"), None)
        example = masked_example(snapshot, attachments, news=news, target_claim=node["text"])
        return {"status": self.status, "model_revision": None,
                "input_revision": snapshot["revision"], "local_target_id": local,
                "target_ids": [local], "log_e": None, "masked_input": example}

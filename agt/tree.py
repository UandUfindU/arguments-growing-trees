from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import copy
import hashlib
import json
import math


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return result


@dataclass
class Node:
    id: str
    kind: str
    text: str
    parent: str | None = None
    relation: str = "supports"
    source: dict = field(default_factory=dict)
    test: dict | None = None
    result: dict | None = None
    prediction: dict | None = None
    local_slot: dict | None = None
    cumulative: dict | None = None
    rationale: str = ""


@dataclass
class Tree:
    hypothesis: str
    root_time: str
    nodes: dict[str, Node] = field(default_factory=dict)
    coverage: dict = field(default_factory=dict)
    horizon: str | None = None
    revision: int = 0
    events: list[dict] = field(default_factory=list)
    seen_events: set[str] = field(default_factory=set)
    seen_lineages: set[str] = field(default_factory=set)

    def add(self, node: Node):
        if node.id in self.nodes:
            raise ValueError("Duplicate node ID")
        if node.kind not in {"claim", "testable_evidence", "textual_evidence"}:
            raise ValueError("Unknown node kind")
        if node.relation not in {"supports", "challenges", "context"}:
            raise ValueError("Unknown edge relation")
        if node.parent is not None and node.parent not in self.nodes:
            raise ValueError("Parent must exist")
        if node.parent is None and self.nodes:
            raise ValueError("Exactly one root is allowed")
        if not node.text.strip():
            raise ValueError("Empty node text")
        self.nodes[node.id] = node

    def path(self, node_id: str) -> list[str]:
        result = []
        while node_id is not None:
            result.append(node_id)
            node_id = self.nodes[node_id].parent
        return result

    def log(self, action: str, **detail):
        self.revision += 1
        self.events.append({"sequence": len(self.events), "revision": self.revision,
                            "action": action, **detail})

    def snapshot(self) -> dict:
        return {"hypothesis": self.hypothesis, "root_time": self.root_time,
                "horizon": self.horizon, "revision": self.revision, "coverage": copy.deepcopy(self.coverage),
                "nodes": {k: asdict(v) for k, v in self.nodes.items()},
                "events": copy.deepcopy(self.events)}

    def digest(self):
        payload = json.dumps(self.snapshot(), sort_keys=True, allow_nan=False)
        return hashlib.sha256(payload.encode()).hexdigest()

    def validate_structure(self):
        if not self.nodes or "root" not in self.nodes:
            raise ValueError("Missing root")
        roots = [n.id for n in self.nodes.values() if n.parent is None]
        if roots != ["root"] or self.nodes["root"].kind != "claim":
            raise ValueError("Exactly one claim root is required")
        for key, node in self.nodes.items():
            if key != node.id:
                raise ValueError("Node ID/key mismatch")
            seen = set()
            current = key
            while current is not None:
                if current in seen or current not in self.nodes:
                    raise ValueError("Cycle or missing parent")
                seen.add(current)
                current = self.nodes[current].parent
            if node.relation not in {"supports", "challenges", "context"}:
                raise ValueError("Unknown relation")
            if node.parent is not None:
                if self.nodes[node.parent].kind != "claim" or not node.rationale.strip():
                    raise ValueError("Every edge must originate from a claim and explain proxy relevance")
    def validate_initial(self):
        self.validate_structure()
        for node in self.nodes.values():
            children = [n for n in self.nodes.values() if n.parent == node.id]
            if node.kind not in {"claim", "testable_evidence"}:
                raise ValueError("Initialization allows only claims and executed proxy tests")
            if node.kind == "claim" and (not children or node.test or node.result):
                raise ValueError("Each claim must have executed proxy descendants, not fabricated local results")
            if node.kind == "testable_evidence":
                if children or not node.test or not node.result:
                    raise ValueError("Every proxy must be an executed leaf")
                result = node.result
                if (result.get("execution") != "scipy_cpu_allowlisted" or
                        not 0 < result.get("p_value", 0) <= 1 or
                        not math.isfinite(result.get("log_e", float("nan")))):
                    raise ValueError("Invalid execution result")

    def proxy_trace(self) -> dict[str, list[str]]:
        """Trace each claim to executed leaves without asserting evidence support."""
        return {node.id: [leaf.id for leaf in self.nodes.values()
                          if leaf.kind == "testable_evidence" and node.id in self.path(leaf.id)]
                for node in self.nodes.values() if node.kind == "claim"}


def affected_paths(tree: dict, attachments: list[str]) -> list[str]:
    affected = set()
    for node_id in attachments:
        while node_id is not None:
            affected.add(node_id)
            node_id = tree["nodes"][node_id]["parent"]
    return sorted(affected)

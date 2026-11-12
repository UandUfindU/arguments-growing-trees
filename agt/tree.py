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


@dataclass
class Tree:
    hypothesis: str
    root_time: str
    nodes: dict[str, Node] = field(default_factory=dict)
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
                "revision": self.revision,
                "nodes": {k: asdict(v) for k, v in self.nodes.items()},
                "events": copy.deepcopy(self.events)}

    def digest(self):
        payload = json.dumps(self.snapshot(), sort_keys=True, allow_nan=False)
        return hashlib.sha256(payload.encode()).hexdigest()

    def validate_initial(self):
        if not self.nodes:
            raise ValueError("Empty tree")
        for node in self.nodes.values():
            children = [n for n in self.nodes.values() if n.parent == node.id]
            if node.kind == "textual_evidence":
                raise ValueError("Initialization requires executed proxy leaves")
            if not children:
                if node.kind != "testable_evidence" or not node.test or not node.result:
                    raise ValueError("Every initial leaf must have an execution record")
                if not math.isfinite(node.result["p_value"]):
                    raise ValueError("Invalid execution result")


def affected_paths(tree: dict, attachments: list[str]) -> list[str]:
    affected = set()
    for node_id in attachments:
        while node_id is not None:
            affected.add(node_id)
            node_id = tree["nodes"][node_id]["parent"]
    return sorted(affected)

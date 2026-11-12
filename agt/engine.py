from __future__ import annotations

import asyncio
import copy

from .statistics import execute_test
from .system1 import UntrainedSystem1
from .tree import Node, Tree, timestamp


class Engine:
    def __init__(self, planner, system1=None):
        self.planner = planner
        self.system1 = system1 or UntrainedSystem1()
        self.history = []
        self.lock = asyncio.Lock()

    def save(self, tree: Tree, stage: str):
        self.history.append({"stage": stage, "tree": tree.snapshot()})

    @staticmethod
    def catalog(datasets: dict, cutoff: str) -> dict:
        return {k: {x: v for x, v in d.items() if x != "path"}
                for k, d in datasets.items()
                if timestamp(d["available_at"]) <= timestamp(cutoff)}

    @staticmethod
    def apply_tests(tree: Tree, specs: list, datasets: dict, cutoff: str,
                    required_parent: str | None = None):
        if not isinstance(specs, list) or len(specs) > 8:
            raise ValueError("Invalid or excessive tests")
        for spec in specs:
            if required_parent and spec["parent"] != required_parent:
                raise ValueError("Background tests must target the attached claim")
            if tree.nodes[spec["parent"]].kind != "claim":
                raise ValueError("Tests must attach to claims")
            plan = spec["plan"]
            if not plan["null"].strip() or not plan["alternative"].strip():
                raise ValueError("Test needs explicit null and alternative")
            if plan["operation"] not in datasets[plan["dataset_id"]]["operations"]:
                raise ValueError("Operation not registered for dataset")
            result = execute_test(plan, datasets, cutoff)
            # Reused samples are explicit evidence references, not new factors.
            reused = [n.id for n in tree.nodes.values() if n.result
                      and n.result.get("data_sha256") == result["data_sha256"]]
            result["shared_data_with"] = reused
            result["overlapping_family_with"] = [
                n.id for n in tree.nodes.values() if n.result
                and n.result.get("data_family") == result["data_family"]]
            tree.add(Node(id=spec["id"], kind="testable_evidence", text=spec["text"],
                          parent=spec["parent"], relation=spec.get("relation", "context"),
                          test=plan, result=result))

    async def initialize(self, hypothesis: str, root_time: str, datasets: dict) -> Tree:
        timestamp(root_time)
        tree = Tree(hypothesis, root_time)
        tree.add(Node("root", "claim", hypothesis))
        plan = await self.planner.plan("initialize", {
            "hypothesis": hypothesis, "root_time": root_time,
            "datasets": self.catalog(datasets, root_time)})
        for spec in plan.get("claims", []):
            if tree.nodes[spec["parent"]].kind != "claim":
                raise ValueError("Claims must attach to claims")
            tree.add(Node(id=spec["id"], kind="claim", text=spec["text"],
                          parent=spec["parent"], relation=spec.get("relation", "context")))
        self.apply_tests(tree, plan["tests"], datasets, root_time)
        tree.validate_initial()
        tree.log("initialized", planner=type(self.planner).__name__)
        self.save(tree, "initialized")
        return tree

    async def ingest(self, tree: Tree, event: dict, datasets: dict):
        """Mount first, invoke S1, then run S2 verification asynchronously.

        Revision compare-and-swap prevents a slow task overwriting a newer tree.
        """
        if timestamp(event["published_at"]) < timestamp(tree.root_time):
            raise ValueError("Runtime event precedes root cutoff")
        if event["id"] in tree.seen_events or event["lineage_id"] in tree.seen_lineages:
            tree.log("duplicate_skipped", event_id=event["id"])
            self.save(tree, "duplicate_skipped")
            return None
        if not event["source_url"].startswith("https://") or not event["text"].strip():
            raise ValueError("A real source URL and excerpt are required")
        start_revision = tree.revision
        placement = await self.planner.plan("attach", {
            "tree": tree.snapshot(), "event": event})
        async with self.lock:
            if start_revision != tree.revision:
                tree.log("stale_attachment_rejected", event_id=event["id"])
                return None
            parent = placement["parent_id"]
            if tree.nodes[parent].kind != "claim":
                raise ValueError("Event must attach to a claim")
            node_id = "event_" + event["id"]
            tree.add(Node(node_id, "claim", placement["claim"], parent,
                          placement.get("relation", "context")))
            delta = (timestamp(event["published_at"])-timestamp(tree.root_time)).total_seconds()
            source = {**event, "delta_seconds_from_root": delta}
            tree.add(Node(node_id+"_text", "textual_evidence", event["text"],
                          node_id, "context", source))
            tree.seen_events.add(event["id"])
            tree.seen_lineages.add(event["lineage_id"])
            tree.log("system2_mounted", event_id=event["id"], node_id=node_id)
            self.save(tree, "mounted")
            prediction = self.system1.predict(tree.snapshot(), [node_id])
            for target in prediction["target_ids"]:
                tree.nodes[target].prediction = {
                    k: v for k, v in prediction.items() if k != "masked_input"}
            tree.log("system1_called", status=prediction["status"], event_id=event["id"])
            self.save(tree, "immediate_update")
            version = tree.revision
            snapshot = tree.snapshot()
        return asyncio.create_task(self.verify(tree, node_id, event, datasets, version, snapshot))

    async def verify(self, tree, attachment_id, event, datasets, version, snapshot):
        try:
            plan = await self.planner.plan("verify", {
                "tree": snapshot, "attachment_id": attachment_id,
                "event": event, "datasets": self.catalog(datasets, event["published_at"])})
            candidate = copy.deepcopy(tree)
            self.apply_tests(candidate, plan["tests"], datasets, event["published_at"], attachment_id)
            async with self.lock:
                if tree.revision != version:
                    tree.log("stale_verification_rejected", event_id=event["id"], expected_revision=version)
                    self.save(tree, "stale_verification")
                    return
                tree.nodes = candidate.nodes
                tree.log("background_verified", event_id=event["id"],
                         tests=len(plan["tests"]), reason=plan.get("reason"))
                self.save(tree, "background_verified")
                prediction = self.system1.predict(tree.snapshot(), [attachment_id])
                for target in prediction["target_ids"]:
                    tree.nodes[target].prediction = {
                        k: v for k, v in prediction.items() if k != "masked_input"}
                tree.log("system1_rescored", status=prediction["status"])
                self.save(tree, "rescored")
        except Exception as exc:
            tree.log("verification_error", error=type(exc).__name__)
            self.save(tree, "verification_error")
            raise

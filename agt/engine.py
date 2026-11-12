from __future__ import annotations

import asyncio
import copy

from .aggregation import aggregate
from .proxy import read_registered_rows, validate_proxy_spec, validate_coverage
from .prompts import VERSION
from .statistics import execute_test
from .system1 import UntrainedSystem1, masked_example
from .tree import Node, Tree, timestamp


class Engine:
    def __init__(self, planner, system1=None):
        self.planner = planner
        self.system1 = system1 or UntrainedSystem1()
        self.history = []
        self.initialization_attempts = []
        self.training_pairs = []
        self.pairing_notes = []
        self.contracts = {}
        self.slots = {}
        self.totals = {}
        self.lock = asyncio.Lock()

    def save(self, tree: Tree, stage: str):
        self.history.append({"stage": stage, "tree": tree.snapshot()})

    @staticmethod
    def catalog(datasets: dict, cutoff: str) -> dict:
        catalog = {}
        for dataset_id, dataset in datasets.items():
            if timestamp(dataset["available_at"]) > timestamp(cutoff):
                continue
            _, rows = read_registered_rows(dataset, cutoff)
            catalog[dataset_id] = {key: value for key, value in dataset.items() if key != "path"}
            catalog[dataset_id]["observed_rows"] = len(rows)
            catalog[dataset_id]["actual_columns"] = list(rows[0])
        return catalog

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
            if plan.get("dataset_id") not in datasets:
                raise ValueError("Unknown registered dataset")
            validate_proxy_spec(spec, datasets[plan["dataset_id"]])
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
                          test=plan, result=result, rationale=spec["rationale"]))

    def build_initial_candidate(self, hypothesis, root_time, datasets, plan):
        """Build privately: no history or caller-visible tree changes before validation."""
        validate_coverage(plan.get("coverage"))
        coverage = copy.deepcopy(plan["coverage"])
        limitations = sorted({item for dataset in self.catalog(datasets, root_time).values()
                              for item in dataset.get("unresolved_aspects", [])})
        if limitations and (coverage["full_hypothesis_covered"] or not coverage["unresolved"]):
            raise ValueError("Registered proxies cannot cover future prospects/returns; retain unresolved scope")
        coverage["registry_limitations"] = limitations
        tree = Tree(hypothesis, root_time, coverage=coverage)
        tree.add(Node("root", "claim", hypothesis))
        pending = list(plan.get("claims", []))
        if len(pending) > 16:
            raise ValueError("Excessive initial claims")
        while pending:
            ready = [spec for spec in pending if spec.get("parent") in tree.nodes]
            if not ready:
                raise ValueError("Claim cycle or nonexistent parent")
            for spec in ready:
                if tree.nodes[spec["parent"]].kind != "claim" or not spec.get("rationale", "").strip():
                    raise ValueError("Claim edge needs a claim parent and relevance rationale")
                tree.add(Node(id=spec["id"], kind="claim", text=spec["text"],
                              parent=spec["parent"], relation=spec["relation"],
                              rationale=spec["rationale"]))
                pending.remove(spec)
        self.apply_tests(tree, plan["tests"], datasets, root_time)
        tree.validate_initial()
        return tree

    async def initialize(self, hypothesis: str, root_time: str, datasets: dict) -> Tree:
        timestamp(root_time)
        context = {"hypothesis": hypothesis, "root_time": root_time,
                   "datasets": self.catalog(datasets, root_time)}
        # Schema retries in the client cannot establish semantic or data validity.
        # At most one separately identified execution/coverage repair is allowed.
        for attempt in range(2):
            plan = await self.planner.plan("initialize", context)
            attempt_record = {"attempt": attempt, "candidate": copy.deepcopy(plan)}
            self.initialization_attempts.append(attempt_record)
            try:
                tree = self.build_initial_candidate(hypothesis, root_time, datasets, plan)
                attempt_record["status"] = "accepted_scoped_execution"
                break
            except (ValueError, KeyError, TypeError) as exc:
                reason = type(exc).__name__ + ": " + str(exc)
                attempt_record.update(status="rejected", reason=reason)
                if hasattr(self.planner, "record_response"):
                    self.planner.record_response({"event": "semantic_repair", **attempt_record})
                if attempt == 1:
                    raise ValueError("Initialization failed after bounded semantic repair: " + reason) from None
                context = {**context, "repair": {"category": "semantic_or_data",
                           "error": reason, "previous_candidate": plan}}
        tree.log("initialized", planner=type(self.planner).__name__, prompt_version=VERSION,
                 semantic_repairs=attempt, proxy_trace=tree.proxy_trace())
        self.save(tree, "initialized")
        return tree

    async def ingest(self, tree: Tree, event: dict, datasets: dict):
        """Mount first, invoke S1, then run S2 verification asynchronously.

        Revision compare-and-swap prevents a slow task overwriting a newer tree.
        """
        if timestamp(event["published_at"]) < timestamp(tree.root_time):
            raise ValueError("Runtime event precedes root cutoff")
        if event["id"] in tree.seen_events or event["lineage_id"] in tree.seen_lineages or event["source_url"] in tree.seen_lineages:
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
            source = {**event, "delta_seconds_from_root": delta,
                      "data_family": datasets.get(event.get("dataset_id"), {}).get("data_family", event.get("dataset_id"))}
            tree.add(Node(node_id+"_text", "textual_evidence", event["text"],
                          node_id, "context", source))
            tree.seen_events.add(event["id"])
            tree.seen_lineages.add(event["lineage_id"])
            tree.seen_lineages.add(event["source_url"])
            tree.log("system2_mounted", event_id=event["id"], node_id=node_id)
            self.save(tree, "mounted")
            prediction = self.system1.predict(tree.snapshot(), [node_id])
            tree.nodes[node_id].prediction = {k:v for k,v in prediction.items() if k != "masked_input"}
            self.slots[node_id] = {"predicted_log_e": prediction["log_e"], "measured_log_e": None}
            tree.nodes[node_id].local_slot = self.slots[node_id]
            self.recompute()
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
                executed = self.replace_local_slot(tree, attachment_id, event, snapshot, plan)
                self.recompute()
                tree.log("local_slot_replaced", tests=len(executed))
                self.save(tree, "measured_replacement")
        except Exception as exc:
            tree.log("verification_error", error=type(exc).__name__)
            self.save(tree, "verification_error")
            raise

    def replace_local_slot(self, tree, attachment_id, event, snapshot, plan):
        executed = [node for node in tree.nodes.values()
                    if node.parent == attachment_id and node.kind == "testable_evidence"]
        if len(executed) != 1:
            self.pairing_notes.append({"event_id": event["id"],
                "reason": plan.get("reason") or "No unique aligned executed local test"})
            return executed
        leaf = executed[0]
        # Prediction and measurement occupy one slot, never two independent factors.
        slot = self.slots[attachment_id]
        slot["measured_log_e"] = leaf.result["log_e"]
        tree.nodes[attachment_id].local_slot = slot
        self.record_training_pair(attachment_id, event, snapshot, leaf)
        return executed

    def record_training_pair(self, attachment_id, event, snapshot, leaf):
        if "fixture" in event.get("text_type", ""):
            self.pairing_notes.append({"event_id": event["id"],
                "reason": "Source-review fixture is not real runtime news"})
            return
        news = next(node["source"] for node in snapshot["nodes"].values()
                    if node["parent"] == attachment_id and node["kind"] == "textual_evidence")
        pair = masked_example(snapshot, [attachment_id], {attachment_id: leaf.result},
                              news=news, target_claim=snapshot["nodes"][attachment_id]["text"])
        pair["label_provenance"] = {
            "executed_test_id": leaf.id, "execution": leaf.result["execution"],
            "data_sha256": leaf.result["data_sha256"]}
        self.training_pairs.append(pair)

    def recompute(self):
        self.totals = {key:aggregate(contract, self.slots) for key,contract in self.contracts.items()}

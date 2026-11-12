"""Offline planned storyboard. Source facts never become statistical tests."""
import argparse
import asyncio
import copy
import json
from pathlib import Path

from .aggregation import evaluate
from .boolean import envelope
from .providers import EvidenceProvider
from .system1 import UntrainedSystem1
from .tree import Tree, Node


def load_scenario():
    return json.loads((Path(__file__).parent / "data/dynamic-governance-v1.json").read_text())


class GovernanceProvider:
    """Implements EvidenceProvider; uncertain day-only dates are never timestamped."""
    def __init__(self, scenario):
        self.documents = copy.deepcopy(scenario["documents"])

    def query(self, query, as_of):
        # Strict public-as-of query: unknown first availability cannot pass.
        from .tree import timestamp
        return [copy.deepcopy(d) for d in self.documents
                if d["first_available_at"] is not None
                and timestamp(d["first_available_at"]) <= timestamp(as_of)
                and query.casefold() in json.dumps(d, ensure_ascii=False).casefold()]

    def storyboard(self, ids):
        """Explicit curated stage selection, NOT a historical retrieval claim."""
        return [copy.deepcopy(d) for d in self.documents if d["id"] in ids]


def ref(key):
    return {"op": "ref", "claim": key}


class Replay:
    def __init__(self, scenario=None):
        self.scenario = copy.deepcopy(scenario or load_scenario())
        self.provider: EvidenceProvider = GovernanceProvider(self.scenario)
        self.tree = Tree(self.scenario["claims"]["root"], "2026-10-28T00:00:00+08:00",
                         horizon=self.scenario["horizon"])
        # root_time is a storyboard reference boundary, not publication time.
        parents = dict(root=None,A="root",D="A",M="A",R="A",B="root",L="B",O="B",C="L",S="L",IC="B")
        for key, parent in parents.items():
            self.tree.add(Node(key, "claim", self.scenario["claims"][key], parent,
                               "context", rationale="预定语义结构；诊断节点未自动参与聚合"))
            args = {"root":["A","B"],"A":["D","M","R"],"B":["L","O"]}.get(key)
            ast = {"op":"AND","args":[ref(x) for x in args]} if args else None
            self.tree.set_expression(key, envelope(self.tree.nodes[key].text,
                                                   self.scenario["horizon"], ast))
        self.tree.freeze_root()
        self.slots = {}
        self.history = []
        self.seen_fragments = set()
        self.distinct_sources = set()

    def snapshot(self, stage, phase, **extra):
        self.tree.validate_expressions()
        self.history.append(dict(stage=stage,phase=phase,tree=self.tree.snapshot(),
                                 local_slots=copy.deepcopy(self.slots),
                                 totals=evaluate(self.tree.snapshot()["nodes"], self.slots),
                                 distinctEvidenceIDs=sorted(self.distinct_sources),**extra))

    def require_initialized(self):
        # No fixture metadata can certify actual execution.
        required = ("D","M","R","L","O")
        missing = [k for k in required if self.slots.get(k,{}).get("positive",{}).get("measured_e") is None]
        if missing or not self.scenario["initialization"]["success"]:
            raise ValueError("incomplete coverage: " + ", ".join(missing))

    def review(self, review):
        if review != self.scenario["review"] or review["status"] != "approved_storyboard_semantics_only":
            raise ValueError("Explicit semantic/scope review required")
        if self.tree.nodes["L"].expression["version"] == 2:
            return
        self.tree.set_expression("L", envelope(self.tree.nodes["L"].text,self.scenario["horizon"],
            {"op":"OR","args":[ref("C"),ref("S")],"weights":review["weights"]},version=2),
            semantic_review=True)
        self.tree.log("reviewed_structure", review=review)

    async def background(self, stage, version):
        await asyncio.sleep(0)
        if self.tree.revision != version:
            self.snapshot(stage, "background_stale_rejected")
            return
        # No registered governance samples: no tests, labels, e or supervision.
        self.snapshot(stage, "background", verification="not_executed_missing_samples",
                      facts_status="source_metadata_only", training_pairs=[])

    async def run(self):
        for stage in self.scenario["stages"]:
            sid = stage["id"]
            if sid == "t0":
                self.snapshot(sid,"initialization",initialization_success=False,
                              missing_proxies=self.scenario["initialization"]["missing_proxies"])
                continue
            if "review" in stage:
                self.review(self.scenario["review"])
            targets = []
            for document in self.provider.storyboard(stage["documents"]):
                for fragment in document["fragments"]:
                    if fragment["id"] in self.seen_fragments:
                        continue
                    self.seen_fragments.add(fragment["id"])
                    target = fragment["target"]
                    if target not in self.tree.nodes:
                        raise ValueError("Unknown target")
                    self.tree.add(Node(fragment["id"],"textual_evidence",fragment["text"],target,
                        "context",source={**document,"fragment_id":fragment["id"],
                                          "assertion_status":fragment["status"]},
                        rationale="用户预置语义片段，非已核验原文或统计样本"))
                    self.distinct_sources.add(document["lineage_id"])
                    targets.append(target)
            self.tree.log("system2_mounted", stage=sid)
            self.snapshot(sid,"mounted",stage_metadata=stage)
            predictions = [UntrainedSystem1().predict(self.tree.snapshot(),[t]) for t in sorted(set(targets))]
            self.snapshot(sid,"immediate",system1=predictions,system1_status="untrained",
                          note="null S1；无低正向e到反向e转换")
            await asyncio.create_task(self.background(sid,self.tree.revision))
        return dict(scenario=self.scenario,history=self.history,api_calls=0,training_executed=False,
                    formal_root_E=None,mode="planned storyboard; no historical availability assertion")


def render(run):
    template = (Path(__file__).parent / "web/governance.html").read_text()
    return template.replace("/* STORY_DATA */ null",
                            json.dumps(run,ensure_ascii=False,allow_nan=False).replace("<","\\u003c"))


def main():
    parser = argparse.ArgumentParser(description="六阶段治理 storyboard；不采集、不调用API")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Use fresh output directory")
    args.output.mkdir(parents=True,exist_ok=True)
    run=asyncio.run(Replay().run())
    (args.output/"run.json").write_text(json.dumps(run,ensure_ascii=False,indent=2))
    (args.output/"index.html").write_text(render(run))
    print(json.dumps(dict(output=str(args.output),snapshots=len(run["history"]),api_calls=0)))


if __name__ == "__main__":
    main()

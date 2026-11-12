from __future__ import annotations

import argparse
import asyncio
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import os

from .engine import Engine
from .providers import FileDatasetProvider, InMemoryEvidenceProvider
from .scenarios import FixturePlanner, scenario
from .system1 import masked_example


async def run(args):
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Use a fresh output directory to preserve existing runs")
    args.output.mkdir(parents=True, exist_ok=True)
    if args.backend == "qwen":
        if not os.environ.get("AGT_QWEN_LEDGER"):
            raise ValueError("Qwen demo requires a persisted AGT_QWEN_LEDGER (16 requests/48000 reserved tokens/25min)")
        from .qwen import QwenSystem2
        planner = QwenSystem2()
    else:
        planner = FixturePlanner()
    engine = Engine(planner)
    s = scenario(args.scenario)
    datasets = FileDatasetProvider(s["datasets"])
    evidence = InMemoryEvidenceProvider([s["event"]])
    hypothesis = args.hypothesis or s["hypothesis"]
    reference_time = args.reference_time or s["root_time"]
    horizon = args.horizon or s["horizon"]
    registered = datasets.registered(s["event"]["published_at"])
    tree = await engine.initialize(hypothesis, reference_time,
                                   datasets.registered(reference_time), horizon=horizon)
    event = evidence.query("", s["event"]["published_at"])[0]
    job = await engine.ingest(tree, event, registered)
    if job:
        await job
    # Demonstrate lineage deduplication with the same source re-delivered.
    await engine.ingest(tree, event, registered)
    examples = engine.training_pairs
    manifest = {"scenario": args.scenario, "backend": args.backend,
                "system1": "untrained",
                "materials": "preloaded source excerpts; no automatic collection",
                "hypothesis": hypothesis, "reference_time": reference_time, "horizon": horizon, "training_executed": False,
                "root_e": engine.totals["root"]["e_value"], "root_probability": None,
                "aggregation_rule": "boolean-v1", "root_status": engine.totals["root"]["status"],
                "execution_sha": subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip(),
                "formal_aggregation": "not_established",
                "calls": planner.calls, "pairing_notes": engine.pairing_notes,
                "local_slots": engine.slots, "boolean_totals": engine.totals,
                "data_sources": {k: {x: v for x, v in d.items() if x != "path"} for k, d in s["datasets"].items()},
                "history": engine.history}
    (args.output / "run.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf8")
    (args.output / "training.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False, allow_nan=False) for x in examples)+"\n", encoding="utf8")
    # A single self-contained file opens without HTTP, and never includes API configuration.
    page = (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf8")
    embedded = json.dumps(manifest, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    page = page.replace("/* RUN_DATA */ null", embedded)
    (args.output / "index.html").write_text(page, encoding="utf8")
    print(json.dumps({"output": str(args.output), "backend": args.backend,
                      "model": getattr(planner, "model", "offline-fixture"),
                      "stages": [x["stage"] for x in engine.history],
                      "api_calls": len(planner.calls), "training_executed": False}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Growing Trees demo")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--hypothesis", help="Unverified natural-language research hypothesis")
    demo.add_argument("--reference-time", help="Timezone-aware public-information cutoff")
    demo.add_argument("--horizon", help="Target research horizon; does not expose future data")
    demo.add_argument("--backend", choices=["fixture", "qwen"], default="fixture")
    demo.add_argument("--scenario", choices=["investment", "discovery"], default="investment")
    demo.add_argument("--output", type=Path, default=Path("runs/demo"))
    serve = sub.add_parser("serve")
    serve.add_argument("--directory", type=Path, default=Path("runs/demo"))
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command == "demo":
        asyncio.run(run(args))
    else:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(args.directory.resolve()))
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
        print(f"Open http://127.0.0.1:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()

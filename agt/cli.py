from __future__ import annotations

import argparse
import asyncio
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil

from .engine import Engine
from .scenarios import FixturePlanner, scenario
from .system1 import masked_example


async def run(args):
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Use a fresh output directory to preserve existing runs")
    args.output.mkdir(parents=True, exist_ok=True)
    if args.backend == "qwen":
        from .qwen import QwenSystem2
        planner = QwenSystem2()
    else:
        planner = FixturePlanner()
    engine = Engine(planner)
    s = scenario(args.scenario)
    tree = await engine.initialize(s["hypothesis"], s["root_time"], s["datasets"])
    job = await engine.ingest(tree, s["event"], s["datasets"])
    if job:
        await job
    # Demonstrate lineage deduplication with the same source re-delivered.
    await engine.ingest(tree, s["event"], s["datasets"])
    examples = engine.training_pairs
    manifest = {"scenario": args.scenario, "backend": args.backend,
                "system1": "untrained", "training_executed": False,
                "root_e": None, "root_probability": None,
                "formal_aggregation": "not_established",
                "calls": planner.calls, "pairing_notes": engine.pairing_notes,
                "local_slots": engine.slots, "contract_totals": engine.totals,
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

from __future__ import annotations

import asyncio
import fcntl
import json
import os
import time
from pathlib import Path

import httpx

from .prompts import system_prompt, repair_prompt
from .planning import parse_plan


class QwenSystem2:
    """OpenAI-compatible Qwen JSON planner, with bounded calls and no fallback."""

    def __init__(self):
        self.base_url = os.environ["AGT_QWEN_BASE_URL"].rstrip("/")
        self.model = os.environ["AGT_QWEN_MODEL"]
        if self.model != "Qwen/Qwen3.8-27B":
            raise ValueError("Select the authorized Qwen/Qwen3.8-27B model ID")
        self.key = os.environ.get("AGT_QWEN_API_KEY", "")
        self.proxy = os.environ.get("AGT_QWEN_PROXY") or None
        self.calls = []
        self.ledger = os.environ.get("AGT_QWEN_LEDGER")

    def reserve_request(self, phase):
        """Reserve maximum output before transport; interrupted attempts still cost budget."""
        if len(self.calls) >= 12:
            raise RuntimeError("Qwen per-run call budget exhausted")
        if not self.ledger:
            return
        with Path(self.ledger).open("a+", encoding="utf8") as out:
            fcntl.flock(out, fcntl.LOCK_EX)
            out.seek(0)
            records = [json.loads(line) for line in out if line.strip()]
            reserved = [r for r in records if r.get("event") == "request_reserved"]
            if len(reserved) >= 36:
                raise RuntimeError("Campaign request budget exhausted (36)")
            if reserved and time.time() - reserved[0]["time"] >= 2400:
                raise RuntimeError("Campaign API wall-time budget exhausted")
            out.write(json.dumps({"event": "request_reserved", "phase": phase,
                                  "time": time.time(), "max_output_tokens": 3000}) + "\n")
            out.flush()

    def record_response(self, record):
        if self.ledger:
            with Path(self.ledger).open("a", encoding="utf8") as out:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")


    async def plan(self, phase: str, context: dict) -> dict:
        instruction = system_prompt(phase)
        if len(self.calls) >= 12:
            raise RuntimeError("Qwen call budget exhausted")
        payload = {"model": self.model, "temperature": 0,
                   "max_tokens": 3000,
                   "chat_template_kwargs": {"enable_thinking": False},
                   "messages": [{"role": "system", "content": "You are System 2 in a research demo. Respond only with one JSON object. " + instruction},
                                {"role": "user", "content": json.dumps(context, ensure_ascii=False)}]}
        if context.get("repair"):
            payload["messages"].append({"role": "user", "content":
                repair_prompt(context["repair"]["error"], semantic=True) +
                " Do not repeat the rejected structure. Keep only operationalizable branches; limitations go in coverage."})
        headers = {"Authorization": "Bearer " + self.key} if self.key else {}
        # Never persist request headers, keys, base URL or credential-bearing errors.
        async with httpx.AsyncClient(timeout=150, proxy=self.proxy, trust_env=False) as client:
            for attempt in range(2):
                self.reserve_request(phase)
                record = {"phase": phase, "status": "in_flight", "model": self.model}
                self.calls.append(record)
                start = time.monotonic()
                try:
                    response = await client.post(self.base_url + "/chat/completions",
                                                 json=payload, headers=headers)
                except httpx.HTTPError as exc:
                    record.update(status="transport_error", error=type(exc).__name__,
                                  seconds=round(time.monotonic() - start, 3))
                    self.record_response(record)
                    raise RuntimeError("Qwen transport failure: " + type(exc).__name__) from None
                record.update(status=response.status_code,
                              seconds=round(time.monotonic() - start, 3))
                obj = response.json() if response.status_code == 200 else {}
                record["usage"] = obj.get("usage", {})
                self.record_response({**record, "event": "response", "response": obj})
                if response.status_code in (429, 500, 502, 503) and attempt == 0:
                    await asyncio.sleep(1)
                    continue
                if response.status_code != 200:
                    raise RuntimeError(f"Qwen HTTP {response.status_code}; inspect private service logs")
                obj = response.json()
                content = obj["choices"][0]["message"]["content"]
                self.calls[-1]["usage"] = obj.get("usage", {})
                try:
                    return parse_plan(content, phase, context)
                except (json.JSONDecodeError, ValueError) as exc:
                    self.record_response({"event": "schema_validation_failure", "phase": phase,
                                          "attempt": attempt, "reason": str(exc)})
                    if attempt == 1:
                        raise RuntimeError("Qwen schema validation failed after bounded repair: " + str(exc)) from None
                    self.record_response({"event": "schema_repair", "phase": phase, "reason": str(exc)})
                    payload["messages"].append({"role": "assistant", "content": content})
                    payload["messages"].append({"role": "user", "content": repair_prompt(str(exc))})
        raise RuntimeError("No Qwen plan")

import json
import os
import unittest
from unittest.mock import patch
import httpx
from agt.qwen import QwenSystem2

class QwenTests(unittest.IsolatedAsyncioTestCase):
    async def test_schema_repair_preserves_model(self):
        payloads = []
        def handler(request):
            payloads.append(json.loads(request.content))
            result = {'tests': [{'plan': {}}]} if len(payloads) == 1 else {'tests': [], 'reason': 'No suitable data'}
            return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(result)}}], 'usage': {'completion_tokens': 10}})
        original = httpx.AsyncClient
        with patch.dict(os.environ, {'AGT_QWEN_BASE_URL': 'http://example.invalid/v1', 'AGT_QWEN_MODEL': 'Qwen/Qwen3.8-27B'}), patch('agt.qwen.httpx.AsyncClient', side_effect=lambda **kw: original(transport=httpx.MockTransport(handler), **kw)):
            planner = QwenSystem2()
            self.assertEqual((await planner.plan('verify', {}))['tests'], [])
            self.assertEqual(len(planner.calls), 2)
            self.assertTrue(all(p['model'] == 'Qwen/Qwen3.8-27B' for p in payloads))
            self.assertIn('Schema error', payloads[1]['messages'][-1]['content'])

    async def test_attach_repairs_evidence_parent(self):
        payloads = []
        def handler(request):
            payloads.append(json.loads(request.content))
            result = {"parent_id": "t_1" if len(payloads) == 1 else "root", "claim": "Scoped update", "relation": "context"}
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(result)}}]})
        original = httpx.AsyncClient
        with patch.dict(os.environ, {"AGT_QWEN_BASE_URL": "http://example.invalid/v1", "AGT_QWEN_MODEL": "Qwen/Qwen3.8-27B"}), patch("agt.qwen.httpx.AsyncClient", side_effect=lambda **kw: original(transport=httpx.MockTransport(handler), **kw)):
            result = await QwenSystem2().plan("attach", {"tree": {"nodes": {"root": {"kind": "claim"}, "t_1": {"kind": "testable_evidence"}}}})
            self.assertEqual(result["parent_id"], "root")
            self.assertEqual(len(payloads), 2)

class RequestBudgetTests(unittest.IsolatedAsyncioTestCase):
    def test_persisted_budget_and_interrupted_reservations(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "api.jsonl"
            with patch.dict(os.environ, {
                "AGT_QWEN_BASE_URL": "http://example.invalid/v1",
                "AGT_QWEN_MODEL": "Qwen/Qwen3.8-27B",
                "AGT_QWEN_LEDGER": str(ledger)}):
                planner = QwenSystem2()
                # Reservations without responses model a killed process.
                for _ in range(36):
                    planner.reserve_request("initialize")
                with self.assertRaisesRegex(RuntimeError, "Campaign request budget"):
                    QwenSystem2().reserve_request("initialize")
                records = [json.loads(line) for line in ledger.read_text().splitlines()]
                self.assertEqual(sum(r["max_output_tokens"] for r in records), 108000)

    async def test_transport_failure_consumes_one_request(self):
        import tempfile
        from pathlib import Path
        def fail(request):
            raise httpx.ConnectError("private transport details", request=request)
        original = httpx.AsyncClient
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "api.jsonl"
            with patch.dict(os.environ, {
                "AGT_QWEN_BASE_URL": "http://example.invalid/v1",
                "AGT_QWEN_MODEL": "Qwen/Qwen3.8-27B",
                "AGT_QWEN_LEDGER": str(ledger)}), patch("agt.qwen.httpx.AsyncClient",
                side_effect=lambda **kw: original(transport=httpx.MockTransport(fail), **kw)):
                planner = QwenSystem2()
                with self.assertRaisesRegex(RuntimeError, "ConnectError"):
                    await planner.plan("verify", {})
                self.assertEqual(len(planner.calls), 1)
                records = [json.loads(line) for line in ledger.read_text().splitlines()]
                self.assertEqual(len([r for r in records if r.get("event") == "request_reserved"]), 1)
                self.assertNotIn("private transport details", ledger.read_text())

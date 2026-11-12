import json
from pathlib import Path
import unittest

class CuratedDemoTests(unittest.TestCase):
    def test_recorded_run_preserves_scope_and_disclaims_formality(self):
        html=Path("demo/index.html").read_text()
        text=html.split("const run=",1)[1]
        run,_=json.JSONDecoder().raw_decode(text)
        self.assertEqual(run["backend"],"qwen")
        self.assertEqual(run["execution_sha"],"1cd88d80a854b7b2b862219e9d589575181b5741")
        self.assertEqual(run["aggregation_rule"],"boolean-v1")
        self.assertFalse(run["training_executed"])
        self.assertEqual(run["root_status"],"provisional")
        self.assertEqual(set(run["local_slots"]),{"c_proxy"})
        roots=[x["tree"]["nodes"]["root"] for x in run["history"]]
        self.assertTrue(all(x["expression"]==roots[0]["expression"] for x in roots))
        self.assertEqual(roots[-1]["text"],run["hypothesis"])
        self.assertIn("纯算术演示 · illustrative",html)
        self.assertNotIn("sequential_product",html)
        self.assertNotIn("AGT_QWEN_BASE_URL",html)
        self.assertTrue(all(x["status"]==200 for x in run["calls"]))

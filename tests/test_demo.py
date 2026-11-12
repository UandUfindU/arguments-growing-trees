import asyncio
import copy
import json
import math
import unittest

from agt.engine import Engine
from agt.scenarios import FixturePlanner, scenario
from agt.statistics import execute_test
from agt.system1 import masked_example, model_text
from agt.train import validate_records
from agt.tree import Node


class DemoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.s = scenario("investment")
        self.engine = Engine(FixturePlanner())
        self.tree = await self.engine.initialize(self.s["hypothesis"], self.s["root_time"], self.s["datasets"])

    async def test_init_and_future_cutoff(self):
        self.tree.validate_initial()
        self.assertNotIn("textual_evidence", [n.kind for n in self.tree.nodes.values()])
        self.assertNotIn("nvda_fy25q1", self.engine.catalog(self.s["datasets"], self.s["root_time"]))
        bad = copy.deepcopy(self.tree.nodes["t_initial"].test)
        bad["dataset_id"] = "nvda_fy25q1"
        with self.assertRaises(ValueError):
            execute_test(bad, self.s["datasets"], self.s["root_time"])

    async def test_runtime_order_and_untrained_and_dedup(self):
        task = await self.engine.ingest(self.tree, self.s["event"], self.s["datasets"])
        await task
        actions = [e["action"] for e in self.tree.events]
        self.assertLess(actions.index("system2_mounted"), actions.index("system1_called"))
        self.assertLess(actions.index("system1_called"), actions.index("background_verified"))
        pred = self.tree.nodes["root"].prediction
        self.assertEqual(pred["status"], "untrained")
        self.assertTrue(all(v is None for v in pred["log_e"].values()))
        count = len(self.tree.nodes)
        event = {**self.s["event"], "id": "another-id"}
        self.assertIsNone(await self.engine.ingest(self.tree, event, self.s["datasets"]))
        self.assertEqual(len(self.tree.nodes), count)

    async def test_entire_path_masked_without_sibling_loss(self):
        result = self.tree.nodes["t_initial"].result
        self.tree.add(Node("sibling", "testable_evidence", "unaffected", "root", result=copy.deepcopy(result)))
        self.tree.nodes["root"].result = {"p_value": 0.123, "e_value": 8888888,
                                         "decision": "significant", "log_e": 15}
        self.tree.events.append({"secret_target": 8888888})
        item = masked_example(self.tree.snapshot(), ["t_initial"], {"t_initial": result})
        self.assertEqual(set(item["target_ids"]), {"root", "c_proxy", "t_initial"})
        for key in item["target_ids"]:
            self.assertEqual(item["tree"]["nodes"][key]["result"], {"masked": True})
        self.assertEqual(item["tree"]["nodes"]["sibling"]["result"], result)
        self.assertNotIn("8888888", model_text(item))
        self.assertEqual(set(item["labels"]), {"t_initial"})
        self.assertEqual(validate_records([item])["observed_targets"], 1)
        self.assertFalse(validate_records([item])["training_executed"])

    async def test_multi_attachment_union(self):
        self.tree.add(Node("c_other", "claim", "Other branch", "root"))
        item = masked_example(self.tree.snapshot(), ["c_other", "t_initial"])
        self.assertEqual(set(item["target_ids"]), {"root", "c_other", "c_proxy", "t_initial"})

    async def test_stale_background_cannot_overwrite(self):
        task = await self.engine.ingest(self.tree, self.s["event"], self.s["datasets"])
        self.tree.log("newer_revision")
        await task
        self.assertNotIn("t_runtime", self.tree.nodes)
        self.assertEqual(self.tree.events[-1]["action"], "stale_verification_rejected")

    async def test_statistical_result_is_real_and_reproducible(self):
        result = self.tree.nodes["t_initial"].result
        from scipy.stats import pearsonr
        r, p = pearsonr([1, 2, 3, 4], [7192, 13507, 18120, 22103])
        self.assertAlmostEqual(result["p_value"], p)
        self.assertAlmostEqual(result["e_value"], .5 / math.sqrt(p))
        self.assertEqual(result["validity_status"], "requires_review")
        self.assertEqual(result["root_aggregation"], "not_established")

    async def test_discovery_reused_data_not_independent(self):
        s = scenario("discovery")
        e = Engine(FixturePlanner())
        t = await e.initialize(s["hypothesis"], s["root_time"], s["datasets"])
        await (await e.ingest(t, s["event"], s["datasets"]))
        self.assertEqual(t.nodes["t_runtime"].result["shared_data_with"], ["t_initial"])


if __name__ == "__main__":
    unittest.main()

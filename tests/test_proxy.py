"""Failure boundaries: proposals are not evidence until data and coverage pass."""
import copy
import tempfile
import unittest
from pathlib import Path

from agt.engine import Engine
from agt.scenarios import FixturePlanner, scenario
from agt.statistics import execute_test


class ProxyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.s = scenario("investment")
        self.engine = Engine(FixturePlanner())
        self.plan = await FixturePlanner().plan("initialize", {
            "hypothesis": self.s["hypothesis"],
            "datasets": self.engine.catalog(self.s["datasets"], self.s["root_time"])})
        self.test = self.plan["tests"][0]["plan"]

    def candidate(self, plan):
        return self.engine.build_initial_candidate(
            self.s["hypothesis"], self.s["root_time"], self.s["datasets"], plan)

    def test_nested_claims_trace_and_orphans(self):
        plan = copy.deepcopy(self.plan)
        plan["claims"].insert(0, {"id": "c_nested", "text": "nested",
            "parent": "c_proxy", "relation": "context", "rationale": "Scoped nested proxy"})
        plan["tests"][0]["parent"] = "c_nested"
        plan["tests"][0]["plan"]["proxy"]["target_claim_id"] = "c_nested"
        tree = self.candidate(plan)
        self.assertEqual(tree.proxy_trace()["root"], ["t_initial"])
        self.assertEqual(tree.proxy_trace()["c_nested"], ["t_initial"])
        plan["tests"] = []
        with self.assertRaisesRegex(ValueError, "descendants"):
            self.candidate(plan)

    def test_invalid_graphs(self):
        for field, value in (("parent", "absent"), ("parent", "c_proxy"),
                             ("id", "root"), ("relation", "tests")):
            plan = copy.deepcopy(self.plan)
            plan["claims"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.candidate(plan)

    def test_mutated_cycle_detected(self):
        tree = self.candidate(self.plan)
        tree.nodes["c_proxy"].parent = "c_proxy"
        with self.assertRaisesRegex(ValueError, "Cycle"):
            tree.validate_initial()

    def test_method_direction_and_fake_columns(self):
        for change in ({"x": "imaginary"}, {"alternative_code": "greater"},
                       {"alternative": "positive only"},
                       {"null": "positive correlation"},
                       {"operation": "chi_square"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                execute_test({**self.test, **change}, self.s["datasets"], self.s["root_time"])

    def test_real_data_boundary(self):
        data = self.s["datasets"]["nvda_fy24"]
        header = "quarter_index,revenue_musd"
        cases = [
            [header, "1,2", "2,3", "3,4"],
            [header, "1,2", "2,2", "3,2", "4,2"],
            [header, "1,2", "1,3", "3,4", "4,5"],
            [header, "1,2", "2,nan", "3,4", "4,5"],
            [header, "1,2", "2,", "3,4", "4,5"],
            ["quarter_index,unknown", "1,2", "2,3", "3,4", "4,5"],
        ]
        for lines in cases:
            csv = chr(10).join(lines) + chr(10)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "data.csv"
                path.write_text(csv)
                with self.subTest(csv=csv), self.assertRaises(ValueError):
                    execute_test(self.test, {"nvda_fy24": {**data, "path": str(path)}},
                                 self.s["root_time"])

    def test_future_data_and_false_coverage(self):
        with self.assertRaises(ValueError):
            execute_test({**self.test, "dataset_id": "nvda_fy25q1"},
                         self.s["datasets"], self.s["root_time"])
        plan = copy.deepcopy(self.plan)
        plan["coverage"]["full_hypothesis_covered"] = True
        with self.assertRaises(ValueError):
            self.candidate(plan)

    async def test_partial_execution_rolls_back(self):
        plan = copy.deepcopy(self.plan)
        bad = copy.deepcopy(plan["tests"][0])
        bad["id"] = "t_bad"
        bad["plan"]["x"] = "invented"
        plan["tests"].append(bad)

        class BrokenPlanner:
            async def plan(self, phase, context):
                return copy.deepcopy(plan)

        engine = Engine(BrokenPlanner())
        with self.assertRaisesRegex(ValueError, "bounded semantic repair"):
            await engine.initialize(self.s["hypothesis"], self.s["root_time"], self.s["datasets"])
        self.assertEqual(engine.history, [])
        self.assertEqual(engine.slots, {})
        self.assertEqual(engine.training_pairs, [])

    def test_proxy_target_and_rationale(self):
        for change in ("target", "rationale"):
            plan = copy.deepcopy(self.plan)
            if change == "target":
                plan["tests"][0]["plan"]["proxy"]["target_claim_id"] = "root"
            else:
                plan["tests"][0]["rationale"] = ""
            with self.assertRaises(ValueError):
                self.candidate(plan)

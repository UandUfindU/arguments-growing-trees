"""Provider contracts and hypothesis-first initialization, without network calls."""
import copy
import unittest

from agt.engine import Engine
from agt.providers import FileDatasetProvider, InMemoryEvidenceProvider
from agt.scenarios import FixturePlanner, scenario


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.s = scenario("investment")

    def test_evidence_provenance_cutoff_and_copies(self):
        provider = InMemoryEvidenceProvider([self.s["event"]])
        self.assertEqual(provider.query("", self.s["root_time"]), [])
        materials = provider.query("revenue", self.s["event"]["published_at"])
        self.assertEqual(len(materials), 1)
        self.assertEqual(materials[0], self.s["event"])
        materials[0]["text"] = "modified"
        self.assertNotEqual(provider.query("", self.s["event"]["published_at"])[0]["text"], "modified")
        for key in ("id", "lineage_id", "published_at", "source_url", "text", "text_type"):
            broken = copy.deepcopy(self.s["event"])
            del broken[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                InMemoryEvidenceProvider([broken])

    def test_catalog_only_public_real_schema(self):
        provider = FileDatasetProvider(self.s["datasets"])
        catalog = provider.catalog(self.s["root_time"])
        self.assertEqual(set(catalog), {"nvda_fy24"})
        self.assertEqual(set(provider.registered(self.s["root_time"])), set(catalog))
        self.assertNotIn("path", catalog["nvda_fy24"])
        self.assertEqual(catalog["nvda_fy24"]["observed_rows"], 4)
        self.assertTrue(set(catalog["nvda_fy24"]["columns"]).issubset(
            catalog["nvda_fy24"]["actual_columns"]))

    async def test_replace_providers_and_start_from_hypothesis(self):
        s = self.s
        class OtherDatasets:
            def registered(self, as_of):
                return FileDatasetProvider(s["datasets"]).registered(as_of)
            def catalog(self, as_of):
                return FileDatasetProvider(s["datasets"]).catalog(as_of)
        class OtherEvidence:
            def query(self, query, as_of):
                return InMemoryEvidenceProvider([s["event"]]).query(query, as_of)
        class InspectPlanner(FixturePlanner):
            async def plan(self, phase, context):
                if phase == "initialize":
                    self.initial_context = copy.deepcopy(context)
                return await super().plan(phase, context)
        planner = InspectPlanner()
        engine = Engine(planner)
        datasets, evidence = OtherDatasets(), OtherEvidence()
        hypothesis = "NVIDIA经营前景在下一季度是否改善？（尚未验证）"
        tree = await engine.initialize(hypothesis, s["root_time"],
                                      datasets.registered(s["root_time"]), horizon="下一季度")
        self.assertEqual(tree.nodes["root"].text, hypothesis)
        self.assertEqual(planner.initial_context["horizon"], "下一季度")
        self.assertNotIn("history", planner.initial_context)
        self.assertNotIn("training", planner.initial_context)
        self.assertEqual(tree.snapshot()["horizon"], "下一季度")
        self.assertTrue(tree.proxy_trace()["root"])
        self.assertFalse(any(n.kind == "textual_evidence" for n in tree.nodes.values()))
        event = evidence.query("", s["event"]["published_at"])[0]
        job = await engine.ingest(tree, event, datasets.registered(event["published_at"]))
        await job
        slot = engine.slots["event_" + event["id"]]
        self.assertIsNone(slot["predicted_log_e"])
        self.assertIn("measured_log_e", slot)

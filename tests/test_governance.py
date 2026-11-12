import asyncio
import copy
import unittest
from agt.governance import Replay, GovernanceProvider, load_scenario
from agt.aggregation import evaluate

class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.replay=Replay()
        self.run=asyncio.run(self.replay.run())

    def test_availability_and_gap(self):
        s=load_scenario()
        self.assertEqual(GovernanceProvider(s).query("", "2026-11-12T23:00:00+08:00"),[])
        for d in s["documents"]:
            self.assertIsNone(d["first_available_at"])
            self.assertIsNone(d["beijing_date"])
            self.assertEqual(d["date_precision"],"day")
        self.assertIn("11/11全文不得回填",s["stages"][1]["gap"])

    def test_lineage_fragments_and_dedup(self):
        last=self.run["history"][-1]
        self.assertEqual(len(last["distinctEvidenceIDs"]),3)
        board=[n for n in last["tree"]["nodes"].values()
               if n["source"].get("document_id")=="board-1108"]
        self.assertEqual(len(board),2)
        self.assertEqual(len({n["source"]["lineage_id"] for n in board}),1)
        count=len(self.replay.seen_fragments)
        asyncio.run(self.replay.run())
        self.assertEqual(len(self.replay.seen_fragments),count)

    def test_target_and_review(self):
        nodes=self.run["history"][-1]["tree"]["nodes"]
        self.assertEqual(nodes["counsel-1110-0"]["parent"],"IC")
        self.assertEqual(nodes["reuters-1111-0"]["source"]["assertion_status"],"reported/alleged")
        self.assertEqual(nodes["B"]["expression"]["ast"]["args"],
                         [{"op":"ref","claim":"L"},{"op":"ref","claim":"O"}])
        self.assertEqual(nodes["L"]["expression"]["version"],2)
        bad=copy.deepcopy(self.replay.scenario["review"]);bad["weights"]=[1,0]
        with self.assertRaises(ValueError):self.replay.review(bad)

    def test_missing_proxies_facts_and_null_s1(self):
        with self.assertRaisesRegex(ValueError,"incomplete coverage"):
            self.replay.require_initialized()
        for h in self.run["history"]:
            self.assertIsNone(h["totals"]["root"]["e_value"])
            self.assertEqual(h["local_slots"],{})
            for p in h.get("system1",[]):
                self.assertIsNone(p["log_e"])
                self.assertEqual(p["status"],"untrained")
                target=p["local_target_id"]
                self.assertEqual(p["masked_input"]["labels"],{})
                self.assertIn("root",p["masked_input"]["mask_ids"])
                self.assertIn(target,p["masked_input"]["mask_ids"])
        for sid in ("early","board","counsel","report","coexist"):
            self.assertEqual([h["phase"] for h in self.run["history"] if h["stage"]==sid],
                             ["mounted","immediate","background"])

    def test_synthetic_slot_replacement_and_polarity(self):
        # SYNTHETIC TEST FIXTURE ONLY; never emitted into the NVIDIA replay.
        nodes=copy.deepcopy(self.run["history"][0]["tree"]["nodes"])
        def slot(key,value):
            return dict(polarity="positive",proposition=nodes[key]["text"],
                        scope=nodes[key]["expression"]["scope"],h0="synthetic null",
                        h1="synthetic alternative",null_for="negative",measured_e=value,
                        predicted_e=None,semantic_status="requires_review",
                        null_status="requires_review",statistical_status="requires_review",
                        sources=["synthetic-test-fixture"])
        slots={k:{"positive":slot(k,4)} for k in ("D","M","R","L","O")}
        self.assertEqual(evaluate(nodes,slots)["root"]["e_value"],4)
        slots["L"]["positive"]=slot("L",0.2)
        self.assertEqual(evaluate(nodes,slots)["root"]["e_value"],0.2)
        nodes["B"]["expression"]["ast"]={"op":"NOT","args":[{"op":"ref","claim":"L"}]}
        self.assertIsNone(evaluate(nodes,slots)["B"]["e_value"])

    def test_stale_background_and_embedded_ui(self):
        from agt.governance import render
        asyncio.run(self.replay.background("report",self.replay.tree.revision-1))
        self.assertEqual(self.replay.history[-1]["phase"],"background_stale_rejected")
        html=render(self.run)
        self.assertNotIn("/* STORY_DATA */ null",html)
        self.assertIn("initialization_success",html)
        self.assertIn("reported/alleged",html)
        self.assertIn("source_url",html)

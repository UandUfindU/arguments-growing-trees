import asyncio
import copy
import math
import unittest
from agt.aggregation import AggregationContract, aggregate
from agt.engine import Engine
from agt.scenarios import FixturePlanner, scenario
from agt.system1 import masked_example, model_text
from agt.train import validate_records

class LocalTests(unittest.IsolatedAsyncioTestCase):
    async def test_aligned_pair_only(self):
        s=scenario("investment"); e=Engine(FixturePlanner())
        t=await e.initialize(s["hypothesis"],s["root_time"],s["datasets"])
        self.assertEqual(e.training_pairs, [])
        await (await e.ingest(t,s["event"],s["datasets"]))
        self.assertEqual(len(e.training_pairs),1)
        x=e.training_pairs[0]
        self.assertEqual(x["news"],s["event"])
        self.assertEqual(len(x["labels"]),1)
        self.assertEqual(validate_records([x])["observed_targets"],1)
        bad=copy.deepcopy(x); bad["labels"]["root"]=4
        with self.assertRaises(ValueError): validate_records([bad])
        slot=e.slots["event_"+s["event"]["id"]]
        self.assertIsNone(slot["predicted_log_e"])
        self.assertIsNotNone(slot["measured_log_e"])
        self.assertEqual(e.totals,{})

    async def test_no_test_is_empty_pairing(self):
        class NoTest(FixturePlanner):
            async def plan(self, phase, context):
                if phase=="verify": return {"tests":[],"reason":"No suitable runtime data"}
                return await super().plan(phase,context)
        s=scenario("investment"); e=Engine(NoTest())
        t=await e.initialize(s["hypothesis"],s["root_time"],s["datasets"])
        await (await e.ingest(t,s["event"],s["datasets"]))
        self.assertEqual(e.training_pairs,[])
        self.assertIn("No suitable",e.pairing_notes[0]["reason"])
        self.assertEqual(validate_records([])["status"],"empty_pairing")

    def test_explicit_contract_replaces_factor(self):
        c=AggregationContract(("old","new"),"FIXTURE: conditional sequential validity assumed")
        slots={"old":{"measured_log_e":math.log(2)},"new":{"predicted_log_e":math.log(3)}}
        self.assertAlmostEqual(aggregate(c,slots)["provisional_e"],6)
        self.assertIsNone(aggregate(c,slots)["measured_e"])
        slots["new"]["measured_log_e"]=math.log(5)
        self.assertAlmostEqual(aggregate(c,slots)["provisional_e"],10)
        self.assertAlmostEqual(aggregate(c,slots)["measured_e"],10)
        self.assertEqual(aggregate(None,slots),{"provisional_e":None,"measured_e":None})
        with self.assertRaises(ValueError): AggregationContract(("a","a"),"invalid")

    async def test_same_url_dedup(self):
        s=scenario("investment"); e=Engine(FixturePlanner())
        t=await e.initialize(s["hypothesis"],s["root_time"],s["datasets"])
        await (await e.ingest(t,s["event"],s["datasets"]))
        self.assertIsNone(await e.ingest(t,{**s["event"],"id":"new","lineage_id":"new"},s["datasets"]))

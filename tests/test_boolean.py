
import asyncio
import copy
import math
import unittest

from agt.aggregation import evaluate
from agt.boolean import envelope
from agt.engine import Engine
from agt.scenarios import FixturePlanner, scenario
from agt.system1 import masked_example, model_text

def ref(key): return {"op":"ref","claim":key}
def op(name, *args, **kw): return {"op":name,"args":list(args),**kw}
def node(key, ast=None):
    return dict(id=key, kind="claim", text=key, parent=None if key=="root" else "root",
                expression=envelope(key,"fixed scope",ast,semantic_status="verified"))
def slot(key, value, negative=False, **kw):
    return dict(polarity="negative" if negative else "positive",
                null_for="positive" if negative else "negative",
                proposition="NOT ("+key+")" if negative else key,
                scope="fixed scope", h0="C" if negative else "not C", h1="not C" if negative else "C",
                measured_e=value, predicted_e=None, semantic_status="verified",
                null_status="verified", statistical_status="verified", sources=[key], **kw)
def setup(ast):
    nodes={k:node(k) for k in ("a","b","c")}
    nodes["root"]=node("root",ast)
    slots={k:{"positive":slot(k,v)} for k,v in zip(("a","b","c"),(8,5,2))}
    return nodes,slots

class BooleanTests(unittest.TestCase):
    def test_and_union_null_minimum(self):
        n,s=setup(op("AND",ref("a"),ref("b"),ref("c")))
        r=evaluate(n,s)["root"]
        self.assertEqual(r["e_value"],2)
        self.assertEqual(r["status"],"formal")
        self.assertEqual(r["optional_stopping"],"not_established")

    def test_or_fixed_mean_not_max_or_product(self):
        n,s=setup(op("OR",ref("a"),ref("b"),weights=[.25,.75]))
        self.assertEqual(evaluate(n,s)["root"]["e_value"],5.75)
        for weights in ([.2,.3],[-.1,1.1],[math.nan,0],[1], [True,False]):
            n["root"]["expression"]["ast"]["weights"]=weights
            with self.subTest(weights=weights),self.assertRaises(ValueError): evaluate(n,s)

    def test_nested_mixed(self):
        n,s=setup(op("OR",op("AND",ref("a"),ref("b")),ref("c"),weights=[.4,.6]))
        self.assertAlmostEqual(evaluate(n,s)["root"]["e_value"],3.2)

    def test_not_missing_and_independent_opposite_test(self):
        n,s=setup(op("NOT",ref("a")))
        r=evaluate(n,s)["root"]
        self.assertIsNone(r["e_value"])
        self.assertIn("negative",r["reasons"][0])
        s["a"]["negative"]=slot("a",3,negative=True)
        self.assertEqual(evaluate(n,s)["root"]["e_value"],3)
        self.assertNotEqual(evaluate(n,s)["root"]["e_value"],1/8)
        s["a"]["negative"]["null_for"]="negative"
        with self.assertRaises(ValueError):evaluate(n,s)

    def test_double_not_and_demorgan(self):
        n,s=setup(op("NOT",op("NOT",ref("a"))))
        self.assertEqual(evaluate(n,s)["root"]["e_value"],8)
        for key,v in (("a",7),("b",3)):
            s[key]["negative"]=slot(key,v,negative=True)
        n["root"]["expression"]["ast"]=op("NOT",op("OR",ref("a"),ref("b"),weights=[.5,.5]))
        self.assertEqual(evaluate(n,s)["root"]["e_value"],3)
        n["root"]["expression"]["ast"]=op("NOT",op("AND",ref("a"),ref("b")))
        self.assertIsNone(evaluate(n,s)["root"]["e_value"])
        n["root"]["expression"]["ast"]["args"][0]["negation_weights"]=[.25,.75]
        self.assertEqual(evaluate(n,s)["root"]["e_value"],4)

    def test_prediction_taints_all_ancestors_and_replacement(self):
        n,s=setup(op("AND",ref("a"),ref("b")))
        s["a"]["positive"].update(measured_e=None,predicted_e=3)
        self.assertEqual(evaluate(n,s)["root"]["status"],"provisional")
        s["a"]["positive"]["measured_e"]=4
        r=evaluate(n,s)["root"]
        self.assertEqual(r["e_value"],4)
        self.assertFalse(r["predicted"])

    def test_semantic_null_statistical_and_selection_gates(self):
        n,s=setup(op("AND",ref("a"),ref("b")))
        for field in ("semantic_status","null_status","statistical_status"):
            test=copy.deepcopy(s);test["a"]["positive"][field]="requires_review"
            self.assertEqual(evaluate(n,test)["root"]["status"],"provisional")
        n["root"]["expression"]["conditions"]={"causal_identification":"requires_review"}
        self.assertEqual(evaluate(n,s)["root"]["status"],"provisional")
        n["root"]["expression"]["conditions"]={}
        n["root"]["expression"]["selection"]="adaptive"
        self.assertEqual(evaluate(n,s)["root"]["status"],"provisional")
        n["root"]["expression"]["semantic_status"]="rejected"
        self.assertIsNone(evaluate(n,s)["root"]["e_value"])

    def test_missing_nonfinite_and_negative(self):
        n,s=setup(op("AND",ref("a"),ref("b")))
        s["a"]["positive"]["measured_e"]=None
        self.assertIsNone(evaluate(n,s)["root"]["e_value"])
        for v in (-1,math.inf,math.nan,True,"8"):
            s["a"]["positive"]["measured_e"]=v
            with self.subTest(v=v),self.assertRaises(ValueError):evaluate(n,s)
        s["a"]["positive"]["measured_e"]=0
        self.assertEqual(evaluate(n,s)["root"]["e_value"],0)

    def test_reference_cycle_depth_and_no_eval_strings(self):
        n,s=setup(ref("missing"))
        with self.assertRaises(ValueError): evaluate(n,s)
        n["root"]["expression"]["ast"]=ref("a")
        n["a"]["expression"]["ast"]=ref("root")
        with self.assertRaises(ValueError): evaluate(n,s)
        n["a"]["expression"]["ast"]=None
        ast=ref("a")
        for _ in range(34):ast=op("NOT",ast)
        n["root"]["expression"]["ast"]=ast
        with self.assertRaises(ValueError): evaluate(n,s)
        n["root"]["expression"]["ast"]="__import__('os')"
        with self.assertRaises(ValueError): evaluate(n,s)

    def test_repeated_source_is_explicit_no_independence_requirement(self):
        n,s=setup(op("OR",ref("a"),ref("b"),weights=[.5,.5]))
        s["b"]["positive"]["sources"]=["a"]
        r=evaluate(n,s)["root"]
        self.assertEqual(r["e_value"],6.5)
        self.assertEqual(r["repeated_sources"],["a"])

    def test_no_default_product_contract(self):
        import agt.aggregation as a
        import inspect
        self.assertFalse(hasattr(a,"AggregationContract"))
        self.assertNotIn("popper_history",inspect.getsource(Engine))
        n,s=setup(op("AND",ref("a"),ref("b")))
        self.assertNotEqual(evaluate(n,s)["root"]["e_value"],40)

class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def prepared(self):
        s=scenario("investment");e=Engine(FixturePlanner())
        t=await e.initialize(s["hypothesis"],s["root_time"],s["datasets"],horizon=s["horizon"])
        return s,e,t

    async def test_same_slot_no_added_condition_and_fixed_root(self):
        s,e,t=await self.prepared()
        expression=copy.deepcopy(t.nodes["root"].expression)
        version_count=copy.deepcopy(t.expression_versions)
        await (await e.ingest(t,s["event"],s["datasets"]))
        self.assertEqual(t.nodes["root"].expression,expression)
        self.assertEqual(t.expression_versions,version_count)
        self.assertEqual(set(e.slots),{"c_proxy"})
        self.assertNotIn("event_"+s["event"]["id"],t.nodes)
        self.assertEqual(e.slots["c_proxy"]["positive"]["execution_test_id"],"t_runtime")
        self.assertEqual(t.hypothesis,s["hypothesis"])
        self.assertEqual(e.totals["root"]["status"],"provisional")

    async def test_expression_versions_cannot_silently_add_condition(self):
        s,e,t=await self.prepared()
        new=copy.deepcopy(t.nodes["root"].expression)
        new["version"]=2
        new["ast"]=op("AND",ref("c_proxy"),ref("c_proxy"))
        with self.assertRaises(ValueError):t.set_expression("root",new)
        t.set_expression("root",new,semantic_review=True)
        t.validate_expressions()
        self.assertEqual(len(t.expression_versions["root"]),2)
        t.nodes["root"].expression["ast"]=ref("c_proxy")
        with self.assertRaises(ValueError):t.validate_expressions()

    async def test_root_scope_and_wording_immutable(self):
        for field in ("hypothesis","root_time","horizon"):
            s,e,t=await self.prepared()
            setattr(t,field,"weakened")
            with self.subTest(field=field),self.assertRaises(ValueError):t.validate_expressions()
        s,e,t=await self.prepared()
        new=copy.deepcopy(t.nodes["root"].expression);new.update(version=2,scope="narrow")
        with self.assertRaises(ValueError):t.set_expression("root",new,semantic_review=True)

    async def test_joint_mask_expression_ancestors_and_hidden_caches(self):
        s,e,t=await self.prepared()
        snap=t.snapshot()
        # Logical reference outside the structural ancestor chain.
        snap["nodes"]["other"]=node("other",ref("c_proxy"))
        snap["nodes"]["other"]["parent"]="root"
        snap["nodes"]["other"]["cumulative"]={"e_value":987654321}
        snap["nodes"]["root"]["rationale"]="cached e=987654321"
        snap["expression_versions"]["leak"]="987654321"
        snap["aggregation_cache"]={"value":987654321}
        x=masked_example(snap,["t_initial"],news=s["event"])
        self.assertIn("other",x["mask_ids"])
        self.assertNotIn("987654321",model_text(x))
        self.assertEqual(x["tree"]["nodes"]["root"]["expression"],snap["nodes"]["root"]["expression"])
        self.assertEqual(x["target_ids"],["t_initial"])

class RepeatedUpdateTests(unittest.IsolatedAsyncioTestCase):
    async def test_latest_event_news_after_same_slot_reuse(self):
        s=scenario("investment"); e=Engine(FixturePlanner())
        t=await e.initialize(s["hypothesis"],s["root_time"],s["datasets"])
        await (await e.ingest(t,s["event"],s["datasets"]))
        # New preloaded excerpt, not an additional independent statistical factor.
        event={**s["event"],"id":"new-excerpt","lineage_id":"distinct-excerpt",
               "source_url":"https://example.invalid/preloaded-test",
               "text":"A different test excerpt for the same scoped claim."}
        class DifferentTest(FixturePlanner):
            async def plan(self,phase,context):
                result=await super().plan(phase,context)
                if phase=="verify":result["tests"][0]["id"]="t_runtime_second"
                return result
        e.planner=DifferentTest()
        await (await e.ingest(t,event,s["datasets"]))
        self.assertEqual(e.training_pairs[-1]["news"]["id"],event["id"])
        self.assertEqual(e.slots["c_proxy"]["positive"]["execution_test_id"],"t_runtime_second")
        self.assertEqual(set(e.slots),{"c_proxy"})

class PromptContractTests(unittest.TestCase):
    def test_atomic_claim_is_not_duplicated_test_record(self):
        from agt.prompts import system_prompt
        p=system_prompt("initialize")
        self.assertIn("claims contains ONLY c_proxy",p)
        self.assertIn("c_proxy.ast=null",p)
        self.assertIn("NOT an AST ref",p)
        self.assertIn("No test ID may appear in claims or expressions",p)

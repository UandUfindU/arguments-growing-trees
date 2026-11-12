"""Small, dated public-data replays; not a benchmark reproduction."""
from __future__ import annotations

from pathlib import Path

from .proxy import HYPOTHESES

DATA = Path(__file__).parent / "data"
NV_NEWS = "https://nvidianews.nvidia.com/news/"


def scenario(name="investment"):
    if name == "investment":
        initial = "2024-02-22T00:00:00+00:00"
        updated = "2024-05-23T00:00:00+00:00"
        common = {"operations": ["pearson"], "data_family": "nvda-quarterly-revenue",
                  "columns": {"quarter_index": "Ordered fiscal-quarter index, not random samples",
                              "revenue_musd": "Reported quarterly revenue, USD millions"},
                  "column_types": {"quarter_index": "number", "revenue_musd": "number"},
                  "observation_key": ["quarter_index"],
                  "sample_requirements": "At least four finite nonconstant paired observations, unique quarter keys",
                  "statistical_assumptions": "Independent bivariate normal pairs; serial dependence is uncorrected and requires review",
                  "testable_claim": "NVIDIA quarterly revenue and fiscal-quarter index have a nonzero linear association in the registered historical sample.",
                  "quantity": "Two-sided Pearson association of fiscal-quarter index and reported revenue",
                  "entity": "NVIDIA", "period": "Registered fiscal quarters (not a future forecast)",
                  "unit": "USD millions",
                  "unresolved_aspects": ["Future business prospects", "Investment returns"],
                  "scope": "Small descriptive trend proxy; no causal or return claim; serial dependence requires review",
                  "suggested_test": {**HYPOTHESES["pearson"], "operation": "pearson", "x": "quarter_index", "y": "revenue_musd"}}
        datasets = {
            "nvda_fy24": {**common, "path": str(DATA / "nvda_fy24.csv"),
                          "available_at": initial,
                          "source_url": NV_NEWS+"nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2024"},
            "nvda_fy25q1": {**common, "path": str(DATA / "nvda_fy25q1.csv"),
                            "available_at": updated,
                            "source_url": NV_NEWS+"nvidia-announces-financial-results-for-first-quarter-fiscal-2025"}}
        event = {"id": "nvda-fy25q1", "lineage_id": "nvda-fy25q1-release",
                 "published_at": updated,
                 "time_precision": "day; conservative following-day UTC availability",
                 "source_url": datasets["nvda_fy25q1"]["source_url"],
                 "text": "NVIDIA reported Q1 FY2025 revenue of $26,044 million, up 18% quarter-over-quarter and 262% year-over-year.",
                 "text_type": "human-normalized factual excerpt", "dataset_id": "nvda_fy25q1"}
        return {"name": name,
                "hypothesis": "NVIDIA's business prospects will improve over the next fiscal quarter.",
                "horizon": "Next fiscal quarter", "root_time": initial, "datasets": datasets, "event": event}
    if name != "discovery":
        raise ValueError("Unknown scenario")
    source = "https://github.com/allenai/discoverybench/blob/c31fcf011e070f021a5f5b906896d0821f6880e8/discoverybench/real/test/introduction_pathways_non-native_plants/temporal_trends_contingency_table.csv"
    cutoff = "2025-01-01T00:00:00+00:00"
    dataset = {"path": str(DATA / "pathways.tsv"), "available_at": cutoff,
               "column_types": {"introduction.period": "category", "pathway": "category", "n": "number"},
               "observation_key": ["introduction.period", "pathway"],
               "sample_requirements": "At least 2x2 nonnegative integer count table with nonempty margins, unique cells and expected counts >=5",
               "statistical_assumptions": "Independent observations and adequate expected counts; domain review required",
               "testable_claim": "Introduction pathways and historical period are associated in the registered Catalonia count table.",
               "quantity": "Period-by-pathway count association",
               "entity": "Catalonia non-native plants", "period": "Historical periods in registered table",
               "unit": "recorded counts",
               "delimiter": "\t", "operations": ["chi_square"], "source_url": source,
               "columns": {"introduction.period": "Period", "pathway": "Introduction route", "n": "Count"},
               "suggested_test": {**HYPOTHESES["chi_square"], "operation": "chi_square", "row": "introduction.period", "column": "pathway", "value": "n"}}
    return {"name": name, "hypothesis": "Introduction pathways and historical period are associated in the registered Catalonia count table.",
            "horizon": "Historical periods in the registered table", "root_time": cutoff, "datasets": {"pathways": dataset},
            "event": {"id": "source-reviewed", "lineage_id": "same-table-review",
                      "published_at": "2025-01-02T00:00:00+00:00", "source_url": source,
                      "text": "The registered source table records period-by-pathway counts for Catalonia. This event reintroduces the same data rather than new independent observations.",
                      "text_type": "source-review fixture, not a historical news event", "dataset_id": "pathways"}}


class FixturePlanner:
    """Explicit offline fixture; never described as a model inference."""
    calls = []

    def __init__(self):
        self.calls = []

    async def plan(self, phase: str, context: dict):
        self.calls.append({"phase": phase, "model": "offline-fixture", "status": "fixture"})
        if phase == "attach":
            return {"parent_id": "c_proxy", "claim": context["testable_claim"], "relation": "context"}
        datasets = context["datasets"]
        dataset_id = context.get("event", {}).get("dataset_id") or next(iter(datasets))
        d = datasets[dataset_id]
        test = {"id": "t_initial" if phase == "initialize" else "t_runtime",
                "parent": "c_proxy" if phase == "initialize" else context["attachment_id"],
                "text": "Execute the registered observational proxy test.", "relation": "context",
                "rationale": "A registered sample association measures only the scoped observational proxy.",
                "plan": {"dataset_id": dataset_id, **d["suggested_test"],
                         "proxy": {"target_claim_id": "c_proxy" if phase == "initialize" else context["attachment_id"],
                                   "quantity": d["quantity"], "entity": d["entity"],
                                   "period": d["period"], "unit": d["unit"],
                                   "available_at": d["available_at"],
                                   "sample_requirements": d["sample_requirements"],
                                   "statistical_assumptions": d["statistical_assumptions"],
                                   "interpretation": "Measures association only in the registered observational sample.",
                                   "limitations": "No causal, future, or investment-return inference."}}}
        if phase == "initialize":
            return {"claims": [{"id": "c_proxy", "text": d["testable_claim"], "parent": "root", "relation": "context",
                                 "rationale": "The sample association is a limited observational operationalization."}],
                    "coverage": {"operationalized": "Registered historical association",
                                 "unresolved": ["Future prospects and investment returns"] if context.get("hypothesis", "").startswith("NVIDIA") else [],
                                 "full_hypothesis_covered": not context.get("hypothesis", "").startswith("NVIDIA")},
                    "tests": [test]}
        return {"tests": [test]}

"""Historical POPPER protocol only. Never imported by the tree engine."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class HistoricalSequentialContract:
    path: tuple[str, ...]
    justification: str
    rule: str = "sequential_product"
    def __post_init__(self):
        if self.rule != "sequential_product" or not self.justification.strip() or len(set(self.path)) != len(self.path):
            raise ValueError("Explicit valid sequential contract required")

def historical_aggregate(contract, slots):
    if contract is None:
        return {"provisional_e": None, "measured_e": None}
    provisional, measured = [], []
    for key in contract.path:
        slot = slots[key]
        actual = slot.get("measured_log_e")
        predicted = slot.get("predicted_log_e")
        measured.append(actual)
        provisional.append(actual if actual is not None else predicted)
    def product(values):
        return None if any(v is None for v in values) else math.exp(sum(values))
    return {"provisional_e": product(provisional), "measured_e": product(measured)}

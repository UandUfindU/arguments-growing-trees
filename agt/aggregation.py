"""One tree evaluator: AND union-null minimum; OR intersection-null fixed mean."""
import math
from .boolean import validate_graph, MAX_DEPTH

def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("Local e must be finite and nonnegative")
    return value

def evaluate(nodes, slots):
    specs = validate_graph(nodes)
    def pending(reason):
        return dict(e_value=None, status="pending", reasons=[reason], predicted=False, sources=[])

    def local(key, negative):
        polarity = "negative" if negative else "positive"
        slot = slots.get(key, {}).get(polarity)
        if not slot:
            return pending(key + ": missing independent " + polarity + " local test")
        required = ("proposition", "scope", "h0", "h1")
        if slot.get("polarity") != polarity or any(not isinstance(slot.get(k), str) or not slot[k].strip() for k in required):
            raise ValueError("Local test requires explicit polarity, proposition, scope and H0/H1")
        expected = ("NOT (" + nodes[key]["text"] + ")") if negative else nodes[key]["text"]
        if slot["proposition"] != expected or slot["scope"] != specs[key].scope:
            raise ValueError("Local test proposition/scope mismatch")
        if slot.get("null_for") != ("positive" if negative else "negative"):
            raise ValueError("H0 polarity must oppose the tested proposition")
        for field in ("measured_e", "predicted_e"):
            if slot.get(field) is not None:
                _number(slot[field])
        measured = slot.get("measured_e")
        predicted = measured is None and slot.get("predicted_e") is not None
        value = slot.get("predicted_e") if predicted else measured
        for name in ("semantic_status", "null_status", "statistical_status"):
            if slot.get(name) not in {"verified", "requires_review", "rejected"}:
                raise ValueError("Missing local validity review status")
        if "rejected" in [slot[n] for n in ("semantic_status", "null_status", "statistical_status")]:
            return pending(key + ": local test review rejected")
        if value is None:
            return pending(key + ": no measured/predicted local e")
        value = _number(value)
        checks = all(slot.get(n) == "verified" for n in ("semantic_status", "null_status", "statistical_status"))
        formal = checks and specs[key].reviewed and not predicted
        return dict(e_value=value, status="formal" if formal else "provisional",
                    reasons=[] if formal else [key + ": prediction or semantic/null/statistical/selection review pending"],
                    predicted=predicted, sources=slot.get("sources", []))

    def claim(key, negative=False, depth=0):
        if depth > MAX_DEPTH:
            raise ValueError("Evaluation depth limit")
        spec = specs[key]
        if spec.semantic_status == "rejected":
            return pending(key + ": expression semantic review rejected")
        result = local(key, negative) if spec.ast is None else expr(spec.ast, negative, depth + 1)
        if not spec.reviewed and result["e_value"] is not None:
            result = {**result, "status": "provisional",
                      "reasons": result["reasons"] + [key + ": expression equivalence/conditions/selection requires_review"]}
        return result

    def expr(ast, negative, depth):
        if depth > MAX_DEPTH:
            raise ValueError("Evaluation depth limit")
        op = ast["op"]
        if op == "ref":
            return claim(ast["claim"], negative, depth + 1)
        if op == "NOT":
            return expr(ast["args"][0], not negative, depth + 1)
        # De Morgan passes polarity down; never transforms any e numerically.
        effective = ({"AND": "OR", "OR": "AND"}[op] if negative else op)
        fixed = ast.get("negation_weights") if negative else ast.get("weights")
        if effective == "OR" and fixed is None:
            return pending("Negated AND needs preset negation_weights for its OR")
        children = [expr(child, negative, depth + 1) for child in ast["args"]]
        sources = [s for c in children for s in c["sources"]]
        reasons = [r for c in children for r in c["reasons"]]
        if any(c["e_value"] is None for c in children):
            return dict(e_value=None, status="pending", reasons=reasons,
                        predicted=any(c["predicted"] for c in children), sources=sources)
        value = (min(c["e_value"] for c in children) if effective == "AND" else
                 math.fsum(w*c["e_value"] for w,c in zip(fixed, children)))
        return dict(e_value=_number(value),
                    status="formal" if all(c["status"] == "formal" for c in children) else "provisional",
                    reasons=reasons, predicted=any(c["predicted"] for c in children), sources=sources)
    for key,polarities in slots.items():
        if key not in specs:
            raise ValueError("Local slot references missing claim")
        for polarity in ("positive", "negative"):
            if polarity in polarities:
                local(key, polarity == "negative")
    totals = {key: claim(key) for key in specs}
    for result in totals.values():
        result["repeated_sources"] = sorted({s for s in result["sources"] if result["sources"].count(s) > 1})
        result["snapshot_only"] = True
        result["optional_stopping"] = "not_established"
    return totals

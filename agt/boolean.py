"""Small Boolean AST boundary. No expression strings or executable model code."""
from dataclasses import dataclass
import math

MAX_DEPTH = 32
STATUSES = {"verified", "requires_review", "rejected"}

def weights(values, size):
    if (not isinstance(values, list) or len(values) != size or
        any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values) or
        not math.isclose(sum(values), 1, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("Weights must be finite, nonnegative and sum to one")

def references(ast, depth=0):
    if depth > MAX_DEPTH or not isinstance(ast, dict):
        raise ValueError("Invalid AST or depth limit")
    op = ast.get("op")
    allowed = {"op", "claim"} if op == "ref" else {"op", "args", "weights", "negation_weights"}
    if set(ast) - allowed:
        raise ValueError("Unknown AST fields (numeric caches/explanations forbidden)")
    if op == "ref":
        if not isinstance(ast.get("claim"), str) or not ast["claim"]:
            raise ValueError("Missing claim reference")
        return {ast["claim"]}
    args = ast.get("args")
    if op not in {"AND", "OR", "NOT"} or not isinstance(args, list):
        raise ValueError("Expected ref/AND/OR/NOT AST")
    if (op == "NOT" and len(args) != 1) or (op != "NOT" and len(args) < 2):
        raise ValueError("Invalid AST arity")
    if op == "OR":
        weights(ast.get("weights"), len(args))
    elif "weights" in ast:
        raise ValueError("Only OR has weights")
    if "negation_weights" in ast:
        if op != "AND":
            raise ValueError("Only AND needs weights for its negated OR")
        weights(ast["negation_weights"], len(args))
    result = set()
    for arg in args:
        result |= references(arg, depth + 1)
    return result

@dataclass(frozen=True)
class Expression:
    version: int
    ast: dict | None
    claim_text: str
    scope: str
    semantic_status: str
    conditions: dict
    selection: str = "pre_observation"

    @classmethod
    def read(cls, value):
        try:
            obj = cls(**value)
        except (TypeError, KeyError):
            raise ValueError("Invalid expression envelope") from None
        if (type(obj.version) is not int or obj.version < 1 or
            not isinstance(obj.claim_text, str) or not obj.claim_text.strip() or
            not isinstance(obj.scope, str) or not obj.scope.strip() or
            obj.semantic_status not in STATUSES or not isinstance(obj.conditions, dict) or
            any(not isinstance(k, str) or v not in STATUSES for k,v in obj.conditions.items()) or
            obj.selection not in {"pre_observation", "adaptive"}):
            raise ValueError("Invalid expression metadata")
        if obj.ast is not None:
            references(obj.ast)
        return obj

    @property
    def reviewed(self):
        return (self.semantic_status == "verified" and self.selection == "pre_observation"
                and all(v == "verified" for v in self.conditions.values()))

def validate_graph(nodes):
    specs = {}
    for key, node in nodes.items():
        if node["kind"] != "claim":
            continue
        spec = Expression.read(node["expression"])
        if spec.claim_text != node["text"]:
            raise ValueError("Expression changed claim wording")
        specs[key] = spec
    def visit(key, stack):
        if key in stack or len(stack) > MAX_DEPTH:
            raise ValueError("Expression reference cycle/depth limit")
        for ref in references(specs[key].ast) if specs[key].ast else ():
            if ref not in specs:
                raise ValueError("Expression must reference an existing claim")
            visit(ref, stack + [key])
    for key in specs:
        visit(key, [])
    return specs

def envelope(text, scope, ast=None, *, version=1, semantic_status="requires_review",
             conditions=None, selection="pre_observation"):
    return dict(version=version, ast=ast, claim_text=text, scope=scope,
                semantic_status=semantic_status, conditions=conditions or {},
                selection=selection)

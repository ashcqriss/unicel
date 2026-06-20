"""A safe arithmetic evaluator.

Used by both the ``calc`` command and the Calculator app. Expressions are
parsed with :mod:`ast` and evaluated by walking a whitelist of node types, so
there is no ``eval`` and no way to reach arbitrary attributes, names or calls —
a small but real win for the "strict permissions" security goal.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Callable

_BIN_OPS: dict[type, Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type, Callable] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Whitelisted names: a handful of math functions and constants.
_FUNCS: dict[str, Callable] = {
    name: getattr(math, name)
    for name in (
        "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
        "log", "log2", "log10", "exp", "floor", "ceil", "fabs",
        "factorial", "gcd", "hypot", "degrees", "radians", "pow",
    )
}
_FUNCS.update({"abs": abs, "round": round, "min": min, "max": max})

_CONSTS: dict[str, float] = {"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf}


class CalcError(ValueError):
    """Raised for invalid or disallowed expressions."""


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalcError("only numbers are allowed")
        return node.value
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise CalcError("operator not allowed")
        return op(_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise CalcError("operator not allowed")
        return op(_eval(node.operand))
    if isinstance(node, ast.Name):
        if node.id in _CONSTS:
            return _CONSTS[node.id]
        raise CalcError(f"unknown name: {node.id}")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
            raise CalcError("function not allowed")
        if node.keywords:
            raise CalcError("keyword arguments not allowed")
        args = [_eval(arg) for arg in node.args]
        return _FUNCS[node.func.id](*args)
    raise CalcError("expression not allowed")


def evaluate(expression: str) -> float:
    """Evaluate an arithmetic ``expression`` and return the numeric result."""
    expression = expression.strip()
    if not expression:
        raise CalcError("empty expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalcError(f"syntax error: {exc.msg}") from exc
    return _eval(tree)


def format_result(value: float) -> str:
    """Format a numeric result, trimming trailing ``.0`` for whole numbers."""
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e16:
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)

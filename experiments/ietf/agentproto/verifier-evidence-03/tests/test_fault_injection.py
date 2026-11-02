"""Actual implementation mutants, loaded in memory without editing the frozen code."""

import ast
from pathlib import Path

import pytest

from test_appraise import NOW, VECTORS

SOURCE_PATH = Path(__file__).resolve().parents[1] / "src/appraise.py"
MUTANTS = [
    ("ignore_withheld_record", "known_omission"),
    ("unavailable_as_satisfied", "resolver_unavailable"),
    ("unavailable_as_unsatisfied", "resolver_unavailable"),
    ("ignore_same_party_control", "same_party_only"),
]


@pytest.mark.parametrize("name,vector_id", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_fault_is_killed(name: str, vector_id: str) -> None:
    tree = ast.parse(SOURCE_PATH.read_text())
    changed = 0
    for node in ast.walk(tree):
        if name == "ignore_withheld_record" and isinstance(node, ast.If):
            if isinstance(node.test, ast.Name) and node.test.id == "omitted":
                node.test = ast.Constant(False)
                changed += 1
        if name == "ignore_same_party_control" and isinstance(node, ast.FunctionDef):
            if node.name == "control":
                guards = [child for child in node.body if isinstance(child, ast.If)]
                guards[1].test = ast.Constant(False)
                changed += 1
        if name.startswith("unavailable_as_") and isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "finish"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "C_RESOLVER"
            ):
                node.args[0] = ast.Constant(name.removeprefix("unavailable_as_").upper())
                changed += 1
    assert changed == 1, f"Mutation target drift: {name}"
    namespace = {"__name__": f"mutant_{name}"}
    exec(compile(ast.fix_missing_locations(tree), f"<mutant:{name}>", "exec"), namespace)
    vector = VECTORS[vector_id]
    result = namespace["appraise"](vector["input"], NOW)
    assert result["result"] != vector["expected"]["result"], f"Mutant survived: {name}"

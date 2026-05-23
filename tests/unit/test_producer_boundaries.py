"""Guardrail: producer-only utilities may be referenced ONLY by producers.

Python has no `protected`/`friend` (a leading underscore is just a
convention the interpreter ignores), so this test enforces the rule at
test time instead: a text-flattening util like ``_clean_text`` is
*producing* final content — the producer's exclusive job — so the
classifier, walker, pre-passes, the assembler, and export must never
touch it.  This is the canonical footnote bug frozen as a check:
``resolve_ref_bodies`` once lived in the classifier and flattened
footnote bodies; it now lives in the footnote producer.

Granularity is per-module (default-deny): every module that references a
producer-only util must appear in ``PRODUCER_MODULES``.  Adding a module
there is a conscious "this module contains producers" assertion, made
visible in review.  The module that *defines* a util is always allowed.

Extend ``PRODUCER_ONLY_UTILS`` as more shared content-production helpers
appear (caption flatteners, etc.).  See the memory note
``clean-text-only-in-producers``.
"""
from __future__ import annotations

import ast
from pathlib import Path

# Utilities only producers may reference.
PRODUCER_ONLY_UTILS: set[str] = {"_clean_text"}

# Module stems (under src/britannica) that contain producers or
# producer-helpers and may therefore reference the utils above.
PRODUCER_MODULES: set[str] = {
    "_layout",       # figure / table layout producers + helpers
    "_image",        # image / img-float / djvu / chart2 producers
    "_tables",       # data / html / compound table producers
    "_leaf",         # math / poem / score producers
    "_ref",          # footnote producer (+ article-scoped resolution)
    "_math_layout",  # math-layout table producers
    "_outline",      # outline producer
}

SRC = Path("src/britannica")


def _references(tree: ast.AST) -> set[str]:
    """Names from PRODUCER_ONLY_UTILS referenced anywhere in `tree`
    (import, attribute access, or bare name).  AST-based, so mentions in
    comments/docstrings are ignored."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in PRODUCER_ONLY_UTILS:
            found.add(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in PRODUCER_ONLY_UTILS:
            found.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in PRODUCER_ONLY_UTILS:
                    found.add(alias.name)
    return found


def test_producer_only_utils_referenced_only_by_producers():
    parsed: dict[Path, ast.AST] = {}
    definer: dict[str, str] = {}  # util name -> defining module stem
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed[path] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in PRODUCER_ONLY_UTILS:
                definer[node.name] = path.stem

    violations: list[str] = []
    for path, tree in parsed.items():
        stem = path.stem
        if stem in PRODUCER_MODULES:
            continue
        refs = {u for u in _references(tree) if definer.get(u) != stem}
        if refs:
            violations.append(f"  {path}: {sorted(refs)}")

    assert not violations, (
        "producer-only utilities referenced outside a producer module.\n"
        "Move the work into the producer that owns the output, or — if "
        "this module really is a producer — add its stem to "
        "PRODUCER_MODULES.\n" + "\n".join(violations)
    )

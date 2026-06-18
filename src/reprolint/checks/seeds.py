from __future__ import annotations
import ast
from pathlib import Path

from reprolint.checks.base import Category, CheckResult, Finding, Severity

SEED_CALLS = {
    ("random", "seed"),
    ("np", "random", "seed"),
    ("numpy", "random", "seed"),
    ("torch", "manual_seed"),
    ("torch", "cuda", "manual_seed"),
    ("torch", "cuda", "manual_seed_all"),
    ("tf", "random", "set_seed"),
    ("tf", "set_random_seed"),
    ("tensorflow", "random", "set_seed"),
}

SEED_EVERYTHING = {
    ("pl", "seed_everything"),
    ("pytorch_lightning", "seed_everything"),
    ("seed_everything",),
    ("transformers", "set_seed"),
    ("set_seed",),
}


def _attr_chain(func: ast.expr) -> tuple[str, ...]:
    """Convert a call's func node into a tuple, e.g. ('np', 'random', 'seed')."""
    parts: list[str] = []
    cur = func
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return tuple(reversed(parts))


def _find_seed_calls(source: str) -> list[tuple[str, int]]:
    """Return (call_name, line_number) for every seed-setting call in a file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    hits: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            chain = _attr_chain(node.func)
            if chain in SEED_CALLS or chain in SEED_EVERYTHING:
                hits.append((".".join(chain), node.lineno))
    return hits


def check_seeds(repo_path: Path) -> CheckResult:
    """Audit whether random seeds are set anywhere in the codebase."""
    reference = "AAAI-25 Reproducibility Checklist (seed-setting item)"
    py_files = list(repo_path.rglob("*.py"))

    all_hits: list[tuple[str, str, int]] = []
    for f in py_files:
        try:
            source = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for call, line in _find_seed_calls(source):
            rel = f.relative_to(repo_path)
            all_hits.append((str(rel), call, line))

    if all_hits:
        findings = [
            Finding(
                message=f"Seed set via {call}",
                severity=Severity.INFO,
                file=file,
                line=line,
            )
            for file, call, line in all_hits[:10]
        ]
        return CheckResult(
            name="Random seeds",
            category=Category.STOCHASTICITY,
            passed=True,
            score=25.0,
            max_score=25.0,
            findings=findings,
            reference=reference,
        )

    # No seeds found anywhere: high-severity reproducibility risk.
    return CheckResult(
        name="Random seeds",
        category=Category.STOCHASTICITY,
        passed=False,
        score=0.0,
        max_score=25.0,
        findings=[
            Finding(
                message="No random seed is set anywhere in the codebase.",
                severity=Severity.HIGH,
                fix="Set seeds early, e.g. random.seed(0); np.random.seed(0); "
                    "torch.manual_seed(0).",
            )
        ],
        reference=reference,
    )
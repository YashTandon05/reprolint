from __future__ import annotations
import ast
from pathlib import Path

from reprolint.checks.base import Category, CheckResult, Finding, Severity

MAX_SCORE = 15.0

DL_FRAMEWORKS = {"torch", "tensorflow", "tf"}
DETERMINISM_CALLS = {
    ("torch", "use_deterministic_algorithms"),
    ("tf", "config", "experimental", "enable_op_determinism"),
    ("tensorflow", "config", "experimental", "enable_op_determinism"),
}


def _attr_chain(node: ast.expr) -> tuple[str, ...]:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return tuple(reversed(parts))


def _analyze(source: str) -> tuple[bool, bool]:
    """Return (uses_dl_framework, enables_determinism) for one file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False, False

    uses_dl = False
    enables = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in DL_FRAMEWORKS:
                    uses_dl = True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in DL_FRAMEWORKS:
                uses_dl = True
        elif isinstance(node, ast.Call):
            if _attr_chain(node.func) in DETERMINISM_CALLS:
                enables = True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    chain = _attr_chain(target)
                    if chain[-1:] == ("deterministic",) and "cudnn" in chain:
                        enables = True
    return uses_dl, enables


def check_nondeterminism(repo_path: Path) -> CheckResult:
    """Check whether deterministic execution is enabled when a DL framework is used."""
    reference = "PyTorch Reproducibility docs; AAAI-25 Reproducibility Checklist (seed item)"
    name = "Deterministic execution"
    cat = Category.STOCHASTICITY

    uses_dl = False
    enables = False
    for f in repo_path.rglob("*.py"):
        try:
            source = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        file_dl, file_enables = _analyze(source)
        uses_dl = uses_dl or file_dl
        enables = enables or file_enables

    if not uses_dl:
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message="No deep-learning framework detected; GPU non-determinism not a concern.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    if enables:
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message="Deterministic execution is explicitly enabled.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    return CheckResult(
        name=name, category=cat, passed=False,
        score=0.0, max_score=MAX_SCORE,
        findings=[Finding(
            message="A deep-learning framework is used but deterministic mode is never enabled. "
                    "Seeds alone do not guarantee reproducible GPU results.",
            severity=Severity.HIGH,
            fix="Call torch.use_deterministic_algorithms(True) (and set "
                "torch.backends.cudnn.deterministic = True), or the TF equivalent.",
        )],
        reference=reference,
    )
from __future__ import annotations
import ast
import re
from pathlib import Path

from reprobe.checks.base import Category, CheckResult, Finding, Severity

MAX_SCORE = 15.0

USER_SPECIFIC = (
    "/home/", "/users/", "/content/", "/root/", "/scratch/",
    "c:\\users", "/content/drive",
)

SYSTEM_ROOTS = (
    "/usr/", "/bin/", "/etc/", "/lib/", "/opt/", "/var/",
    "/sys/", "/proc/", "/dev/", "/sbin/",
)
_WIN_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
_PATHY = re.compile(r"[\w\-. /]+")


def _is_url(s: str) -> bool:
    return "://" in s


def _looks_like_abs_path(s: str) -> bool:
    if not s or _is_url(s):
        return False
    if _WIN_DRIVE.match(s):
        return True
    if s.startswith("/"):
        low = s.lower()
        if any(low.startswith(r) for r in SYSTEM_ROOTS):
            return False
        segments = [seg for seg in s.split("/") if seg]
        if len(segments) >= 2 and _PATHY.fullmatch(s):
            return True
    return False


def _severity(s: str) -> Severity:
    low = s.lower()
    if any(marker in low for marker in USER_SPECIFIC):
        return Severity.HIGH
    return Severity.MEDIUM


def _scan_file(source: str) -> list[tuple[str, int, Severity]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    hits: list[tuple[str, int, Severity]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _looks_like_abs_path(node.value):
                hits.append((node.value, node.lineno, _severity(node.value)))
    return hits


def check_paths(repo_path: Path) -> CheckResult:
    """Flag absolute filesystem paths hardcoded in source (configuration debt)."""
    # TODO : Need to check reference
    reference = "Sculley et al. (2015), Hidden Technical Debt in ML Systems (configuration debt)"
    name = "Hardcoded paths"
    cat = Category.CODE_QUALITY

    findings: list[Finding] = []
    n_high = n_med = 0
    for f in repo_path.rglob("*.py"):
        try:
            source = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = f.relative_to(repo_path)
        for value, line, sev in _scan_file(source):
            if sev == Severity.HIGH:
                n_high += 1
            else:
                n_med += 1
            findings.append(Finding(
                message=f"Hardcoded absolute path: {value!r}",
                severity=sev,
                file=str(rel),
                line=line,
                fix="Use a relative path, a config value, or an environment variable.",
            ))

    if not findings:
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message="No hardcoded absolute paths found.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    penalty = n_high * 5 + n_med * 3
    score = max(0.0, MAX_SCORE - penalty)
    return CheckResult(
        name=name, category=cat, passed=False,
        score=score, max_score=MAX_SCORE,
        findings=findings[:10],
        reference=reference,
    )
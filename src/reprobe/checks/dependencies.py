from __future__ import annotations
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from packaging.requirements import InvalidRequirement, Requirement

from reprobe.checks.base import Category, CheckResult, Finding, Severity

MAX_SCORE = 20.0
LOCK_FILES = ("uv.lock", "poetry.lock")


def _classify(spec_str: str) -> str:
    """Classify a requirement as pinned / loose / unpinned / unparseable."""
    try:
        req = Requirement(spec_str)
    except InvalidRequirement:
        return "unparseable"
    if not req.specifier:
        return "unpinned"
    operators = {s.operator for s in req.specifier}
    if operators <= {"==", "==="}:
        return "pinned"
    return "loose"


def _collect_deps(repo: Path) -> tuple[list[str], bool]:
    """Gather declared dependencies. Returns (deps, manifest_found)."""
    deps: list[str] = []
    manifest_found = False

    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        manifest_found = True
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            deps += data.get("project", {}).get("dependencies", [])
        except (tomllib.TOMLDecodeError, OSError):
            pass

    requirements = repo / "requirements.txt"
    if requirements.exists():
        manifest_found = True
        try:
            for line in requirements.read_text(encoding="utf-8").splitlines():
                line = line.split("#")[0].strip()
                if line and not line.startswith("-"):
                    deps.append(line)
        except OSError:
            pass

    return deps, manifest_found


def _find_lockfile(repo: Path) -> str | None:
    for name in LOCK_FILES:
        if (repo / name).exists():
            return name
    return None


def check_dependencies(repo_path: Path) -> CheckResult:
    """Audit whether dependencies are reproducibly specified."""
    # TODO Verify Sculley Paper
    reference = "AAAI-25 Reproducibility Checklist (library names & versions); Sculley et al. (2015)"
    name = "Dependency pinning"
    cat = Category.ENVIRONMENT

    lockfile = _find_lockfile(repo_path)
    if lockfile:
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message=f"Lock file present ({lockfile}) — transitive deps are pinned.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    deps, manifest_found = _collect_deps(repo_path)

    if not manifest_found:
        return CheckResult(
            name=name, category=cat, passed=False,
            score=0.0, max_score=MAX_SCORE,
            findings=[Finding(
                message="No dependency manifest found (pyproject.toml / requirements.txt).",
                severity=Severity.MEDIUM,
                fix="Declare dependencies in pyproject.toml or requirements.txt.",
            )],
            reference=reference,
        )

    if not deps:
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message="No third-party dependencies declared.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    findings: list[Finding] = []
    pinned = 0
    for d in deps:
        kind = _classify(d)
        if kind == "pinned":
            pinned += 1
        elif kind in ("loose", "unpinned"):
            findings.append(Finding(
                message=f"'{d}' is {kind} (not exactly pinned).",
                severity=Severity.MEDIUM if kind == "loose" else Severity.HIGH,
                fix="Pin to an exact version (e.g. 'pkg==1.2.3') or commit a lock file.",
            ))

    fraction = pinned / len(deps)
    score = round(MAX_SCORE * fraction, 1)
    passed = pinned == len(deps)

    return CheckResult(
        name=name, category=cat, passed=passed,
        score=score, max_score=MAX_SCORE,
        findings=findings[:10],
        reference=reference,
    )
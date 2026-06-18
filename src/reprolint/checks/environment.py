from __future__ import annotations
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from reprolint.checks.base import Category, CheckResult, Finding, Severity

MAX_SCORE = 10.0


def _detect(repo: Path) -> tuple[bool, bool, bool, bool]:
    """Return (has_docker, has_conda, has_pyversion, has_requires_python)."""
    has_docker = (repo / "Dockerfile").exists() or any(repo.glob("*.dockerfile"))
    has_conda = (repo / "environment.yml").exists() or (repo / "environment.yaml").exists()
    has_pyversion = (repo / ".python-version").exists() or (repo / "runtime.txt").exists()

    has_requires_python = False
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            has_requires_python = "requires-python" in data.get("project", {})
        except (tomllib.TOMLDecodeError, OSError):
            pass
    return has_docker, has_conda, has_pyversion, has_requires_python


def check_environment(repo_path: Path) -> CheckResult:
    """Check whether the runtime environment is captured for reproduction."""
    reference = "AAAI-25 Reproducibility Checklist (computing infrastructure); Raff (2019)"
    name = "Environment capture"
    cat = Category.ENVIRONMENT

    has_docker, has_conda, has_pyversion, has_requires_python = _detect(repo_path)

    if has_docker or has_conda:
        mechanism = "Dockerfile" if has_docker else "conda environment.yml"
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message=f"Environment captured via {mechanism}.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    if has_pyversion:
        return CheckResult(
            name=name, category=cat, passed=True,
            score=7.0, max_score=MAX_SCORE,
            findings=[Finding(
                message="Python version is pinned, but no container or conda env is provided.",
                severity=Severity.LOW,
                fix="Add a Dockerfile or environment.yml to capture the full environment.",
            )],
            reference=reference,
        )

    if has_requires_python:
        return CheckResult(
            name=name, category=cat, passed=False,
            score=4.0, max_score=MAX_SCORE,
            findings=[Finding(
                message="Only a Python version range is declared; the full environment is not captured.",
                severity=Severity.MEDIUM,
                fix="Add a Dockerfile, environment.yml, or a pinned .python-version.",
            )],
            reference=reference,
        )

    return CheckResult(
        name=name, category=cat, passed=False,
        score=0.0, max_score=MAX_SCORE,
        findings=[Finding(
            message="No environment capture found (no Dockerfile, conda env, or Python version pin).",
            severity=Severity.HIGH,
            fix="Add a Dockerfile or environment.yml so others can reproduce your setup.",
        )],
        reference=reference,
    )
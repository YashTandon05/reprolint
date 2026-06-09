from __future__ import annotations
from pathlib import Path

from reprobe.checks.base import Category, CheckResult, Finding, Severity

MAX_SCORE = 15.0
RAW_SIZE_THRESHOLD = 5 * 1024 * 1024

DATA_EXTS = {
    ".csv", ".tsv", ".parquet", ".feather", ".h5", ".hdf5",
    ".npy", ".npz", ".pkl", ".pt", ".pth", ".ckpt",
}


def _detect_tracking(repo: Path) -> tuple[bool, bool]:
    """Return (has_dvc, has_lfs)."""
    has_dvc = (
        (repo / ".dvc").is_dir()
        or (repo / "dvc.yaml").exists()
        or any(repo.rglob("*.dvc"))
    )
    has_lfs = False
    gitattributes = repo / ".gitattributes"
    if gitattributes.exists():
        try:
            has_lfs = "filter=lfs" in gitattributes.read_text(
                encoding="utf-8", errors="ignore"
            )
        except OSError:
            pass
    return has_dvc, has_lfs


def _find_data_files(repo: Path) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for f in repo.rglob("*"):
        if not f.is_file() or ".git" in f.parts:
            continue
        if f.suffix.lower() in DATA_EXTS:
            try:
                out.append((str(f.relative_to(repo)), f.stat().st_size))
            except OSError:
                continue
    return out


def check_data_tracking(repo_path: Path) -> CheckResult:
    """Check whether datasets are versioned rather than silently assumed."""
    # TODO : Check the references
    reference = "Sculley et al. (2015), data dependencies; Raff (2019)"
    name = "Data tracking"
    cat = Category.DATA_INTEGRITY

    has_dvc, has_lfs = _detect_tracking(repo_path)
    if has_dvc or has_lfs:
        mechanism = "DVC" if has_dvc else "git-LFS"
        return CheckResult(
            name=name, category=cat, passed=True,
            score=MAX_SCORE, max_score=MAX_SCORE,
            findings=[Finding(
                message=f"Data is version-tracked via {mechanism}.",
                severity=Severity.INFO,
            )],
            reference=reference,
        )

    data_files = _find_data_files(repo_path)
    big_raw = [(p, s) for p, s in data_files if s > RAW_SIZE_THRESHOLD]

    if big_raw:
        findings = [
            Finding(
                message=f"Large data file committed raw: {p} ({s // (1024*1024)} MB)",
                severity=Severity.HIGH,
                file=p,
                fix="Track large data with DVC or git-LFS instead of committing it directly.",
            )
            for p, s in big_raw[:10]
        ]
        return CheckResult(
            name=name, category=cat, passed=False,
            score=0.0, max_score=MAX_SCORE,
            findings=findings,
            reference=reference,
        )

    if data_files:
        return CheckResult(
            name=name, category=cat, passed=False,
            score=round(MAX_SCORE / 2, 1), max_score=MAX_SCORE,
            findings=[Finding(
                message=f"{len(data_files)} data file(s) present but not tracked with DVC or git-LFS.",
                severity=Severity.MEDIUM,
                fix="Version datasets with DVC or git-LFS so others can obtain the exact data.",
            )],
            reference=reference,
        )

    return CheckResult(
        name=name, category=cat, passed=True,
        score=MAX_SCORE, max_score=MAX_SCORE,
        findings=[Finding(
            message="No untracked data artifacts detected.",
            severity=Severity.INFO,
        )],
        reference=reference,
    )
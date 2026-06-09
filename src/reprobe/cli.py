from __future__ import annotations
from pathlib import Path
import typer
from rich.console import Console

from reprobe.github import cloned, is_github_url, repo_display_name
from reprobe.checks.data_tracking import check_data_tracking
from reprobe.checks.dependencies import check_dependencies
from reprobe.checks.environment import check_environment
from reprobe.checks.nondeterminism import check_nondeterminism
from reprobe.checks.paths import check_paths
from reprobe.checks.seeds import check_seeds
from reprobe.report import render
from reprobe.scorer import score

app = typer.Typer(add_completion=False)
console = Console()

CHECKS = (
    check_seeds,
    check_dependencies,
    check_paths,
    check_nondeterminism,
    check_data_tracking,
    check_environment,
)


@app.command()
def audit(
    target: str = typer.Argument(..., help="Local path or GitHub URL to audit"),
    min_score: int = typer.Option(None, "--min-score", help="Minimum passing score (0-100)"),
    fail: bool = typer.Option(False, "--fail", help="Exit with code 1 if score is below --min-score"),
    output: str = typer.Option(None, "--output", help="Save report to a file"),
) -> None:
    """Audit a machine learning repository for reproducibility."""
    if is_github_url(target):
        display = repo_display_name(target)
        console.print(f"\n[bold cyan]reprobe[/bold cyan] — cloning [yellow]{display}[/yellow] ...\n")
        try:
            with cloned(target) as repo_path:
                _run_audit(repo_path, target=display, min_score=min_score, fail=fail, output=output)
        except RuntimeError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=2)
    else:
        repo_path = Path(target).expanduser().resolve()
        if not repo_path.exists():
            console.print(f"[red]Path does not exist:[/red] {repo_path}")
            raise typer.Exit(code=2)
        console.print(f"\n[bold cyan]reprobe[/bold cyan] — auditing [yellow]{repo_path}[/yellow]\n")
        _run_audit(repo_path, target=str(repo_path), min_score=min_score, fail=fail, output=output)


def _run_audit(
    repo_path: Path,
    *,
    target: str,
    min_score: int | None,
    fail: bool,
    output: str | None,
) -> None:
    results = [check(repo_path) for check in CHECKS]
    scorecard = score(results)

    if output:
        out_console = Console(file=open(output, "w"), highlight=False)
        render(scorecard, out_console)
        console.print(f"[dim]Report saved to {output}[/dim]")
    else:
        render(scorecard, console)

    if fail and min_score is not None and scorecard.total < min_score:
        console.print(
            f"[red]Score {scorecard.total:.0f} is below minimum {min_score} — failing.[/red]"
        )
        raise typer.Exit(code=1)


def main() -> None:
    app()
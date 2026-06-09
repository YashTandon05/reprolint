from __future__ import annotations
from pathlib import Path
import typer
from rich.console import Console

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
    target: str = typer.Argument(..., help="Local path to the repository to audit"),
) -> None:
    """Audit a machine learning repository for reproducibility."""
    repo_path = Path(target).expanduser().resolve()
    if not repo_path.exists():
        console.print(f"[red]Path does not exist:[/red] {repo_path}")
        raise typer.Exit(code=2)

    console.print(
        f"\n[bold cyan]reprobe[/bold cyan] — auditing [yellow]{repo_path}[/yellow]\n"
    )

    results = [check(repo_path) for check in CHECKS]
    scorecard = score(results)
    render(scorecard, console)


def main() -> None:
    app()
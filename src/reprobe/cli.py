from __future__ import annotations
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from reprobe.checks.seeds import check_seeds
from reprobe.checks.dependencies import check_dependencies
from reprobe.checks.paths import check_paths
from reprobe.checks.nondeterminism import check_nondeterminism
from reprobe.checks.data_tracking import check_data_tracking
from reprobe.checks.environment import check_environment

app = typer.Typer(add_completion=False)
console = Console()


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

    results = [check_seeds(repo_path), 
               check_dependencies(repo_path), 
               check_paths(repo_path), 
               check_nondeterminism(repo_path),
               check_data_tracking(repo_path),
               check_environment(repo_path)]

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Category")
    table.add_column("Result")
    table.add_column("Score", justify="right")

    for r in results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(
            r.name, r.category.value, status, f"{r.score:.0f}/{r.max_score:.0f}"
        )

    console.print(table)

    for r in results:
        for f in r.findings:
            loc = ""
            if f.file:
                loc = f" [dim]({f.file}:{f.line})[/dim]" if f.line else f" [dim]({f.file})[/dim]"
            console.print(f"  [{f.severity.value}] {f.message}{loc}")
            if f.fix:
                console.print(f"        [dim]fix: {f.fix}[/dim]")
        if r.reference:
            console.print(f"  [dim italic]ref: {r.reference}[/dim italic]")

    console.print()


def main() -> None:
    app()
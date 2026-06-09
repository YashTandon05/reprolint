import typer
from rich.console import Console
from pathlib import Path

app = typer.Typer()
console = Console()

@app.command()
def audit(
    target: str = typer.Argument(..., help="Local path or GitHub URL to audit"),
    min_score: int = typer.Option(None, "--min-score", help="Minimum score threshold"),
    fail: bool = typer.Option(False, "--fail", help="Exit with code 1 if score is below min-score"),
    output: str = typer.Option(None, "--output", help="Save report to a file"),
):
    """
    Audit a machine learning repository for reproducibility.
    """
    console.print(f"\n[bold cyan]reprobe[/bold cyan] — auditing [yellow]{target}[/yellow]\n")
    console.print("[dim]Coming soon: full audit results[/dim]")

def main():
    app()
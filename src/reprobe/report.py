from __future__ import annotations
from rich.console import Console
from rich.table import Table

from reprobe.checks.base import Severity
from reprobe.scorer import Scorecard

_SEVERITY_STYLE = {
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFO: "dim",
}


def _bar(fraction: float, width: int = 10) -> str:
    filled = round(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _verdict_style(total: float) -> str:
    if total >= 80:
        return "bold green"
    if total >= 60:
        return "bold yellow"
    if total >= 40:
        return "bold dark_orange"
    return "bold red"


def render(scorecard: Scorecard, console: Console) -> None:
    # 1. Per-check results table.
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Category")
    table.add_column("Result")
    table.add_column("Score", justify="right")
    for r in scorecard.results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(
            r.name, r.category.value, status, f"{r.score:.0f}/{r.max_score:.0f}"
        )
    console.print(table)

    # 2. Category breakdown.
    console.print("\n[bold]Category breakdown[/bold]")
    for cs in scorecard.categories:
        pct = cs.fraction * 100
        console.print(
            f"  {cs.category.value:16s} {_bar(cs.fraction)} "
            f"{cs.earned:.0f}/{cs.possible:.0f}  ({pct:.0f}%)"
        )

    # 3. Overall score and verdict.
    style = _verdict_style(scorecard.total)
    console.print(
        f"\n[bold]Overall score:[/bold] [{style}]{scorecard.total:.0f}/100[/{style}]"
    )
    console.print(f"[{style}]{scorecard.verdict}[/{style}]")

    # 4. Findings worth surfacing (skip pure INFO).
    notable = [
        (r, f)
        for r in scorecard.results
        for f in r.findings
        if f.severity != Severity.INFO
    ]
    if notable:
        console.print("\n[bold]Findings[/bold]")
        for r, f in notable:
            sev_style = _SEVERITY_STYLE.get(f.severity, "white")
            loc = ""
            if f.file:
                loc = f" [dim]({f.file}:{f.line})[/dim]" if f.line else f" [dim]({f.file})[/dim]"
            console.print(f"  [{sev_style}][{f.severity.value}][/{sev_style}] {f.message}{loc}")
            if f.fix:
                console.print(f"        [dim]fix: {f.fix}[/dim]")

    console.print()
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from analyzers.base import Finding

_console = Console()

_ICONS = {"critical": "🔴", "warning": "🟡", "suggestion": "🟢"}
_LABELS = {"critical": "CRÍTICO", "warning": "ADVERT.", "suggestion": "SUGER."}
_COLORS = {"critical": "red", "warning": "yellow", "suggestion": "green"}


def render_report(file_path: Path, findings: list[Finding]) -> None:
    _console.print()
    _console.rule(f"[bold cyan]📊 Reporte de Calidad: {file_path}[/bold cyan]")

    if not findings:
        _console.print("[bold green]  ✅ Sin hallazgos. ¡Código limpio![/bold green]\n")
        return

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on dark_blue",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("Sev.", width=11, no_wrap=True)
    table.add_column("Categoría", width=12, no_wrap=True)
    table.add_column("Línea", width=6, justify="right", no_wrap=True)
    table.add_column("Hallazgo", min_width=34)
    table.add_column("Sugerencia", min_width=34)

    for f in findings:
        icon = _ICONS[f.severity]
        label = _LABELS[f.severity]
        color = _COLORS[f.severity]
        table.add_row(
            f"[{color}]{icon} {label}[/{color}]",
            f.category,
            str(f.line),
            f.message,
            f"[dim]{f.suggestion}[/dim]",
        )

    _console.print(table)

    counts = {s: 0 for s in ("critical", "warning", "suggestion")}
    for f in findings:
        counts[f.severity] += 1

    _console.print(
        f"\n  Total: "
        f"[bold red]{counts['critical']} crítico(s)[/bold red]  "
        f"[bold yellow]{counts['warning']} advertencia(s)[/bold yellow]  "
        f"[bold green]{counts['suggestion']} sugerencia(s)[/bold green]\n"
    )

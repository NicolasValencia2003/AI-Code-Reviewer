#!/usr/bin/env python3
"""AI Code Reviewer — Analiza archivos de código y genera reportes de calidad."""

from pathlib import Path

import typer
from rich.console import Console

from analyzers import analyze_clean_code, analyze_complexity, analyze_security
from analyzers.base import Finding
from reporters import render_report

app = typer.Typer(
    name="reviewer",
    help="Analiza archivos de código (.py .js .ts .java) y reporta vulnerabilidades, "
    "problemas de clean code y complejidad ciclomática.",
    add_completion=False,
)

_console = Console()
_SUPPORTED = {".py", ".js", ".ts", ".java"}
_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2}


@app.command()
def review(
    files: list[Path] = typer.Argument(..., help="Uno o más archivos de código a analizar"),
) -> None:
    """Analiza archivos de código y genera un reporte de calidad clasificado por severidad."""
    for file_path in files:
        _process_file(file_path)


def _process_file(file_path: Path) -> None:
    if not file_path.exists():
        _console.print(f"[red]✗ Archivo no encontrado: '{file_path}'[/red]")
        return
    if file_path.suffix not in _SUPPORTED:
        _console.print(
            f"[yellow]⚠ Extensión '{file_path.suffix}' no soportada. "
            f"Lenguajes: {', '.join(sorted(_SUPPORTED))}[/yellow]"
        )
        return
    code = file_path.read_text(encoding="utf-8", errors="replace")
    findings = _run_analyzers(code, file_path)
    render_report(file_path, findings)


def _run_analyzers(code: str, file_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(analyze_security(code, file_path))
    findings.extend(analyze_clean_code(code, file_path))
    findings.extend(analyze_complexity(code, file_path))
    findings.sort(key=lambda f: (_SEVERITY_ORDER.get(f.severity, 3), f.line))
    return findings


if __name__ == "__main__":
    app()

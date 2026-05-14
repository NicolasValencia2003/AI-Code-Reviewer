"""Análisis de código con Claude (Anthropic)."""

import json
import os
from pathlib import Path

import anthropic

from .base import Finding

_client: anthropic.AsyncAnthropic | None = None

_SYSTEM = (
    "Eres un experto revisor de código. Analiza el código recibido y detecta problemas en tres áreas:\n"
    "1. Seguridad: inyección SQL, XSS, command injection, credenciales hardcodeadas, eval(), etc.\n"
    "2. Clean Code: funciones largas, nombres poco descriptivos, duplicación, números mágicos, etc.\n"
    "3. Complejidad: lógica muy anidada, funciones con muchas responsabilidades, condicionales complejos.\n\n"
    "Responde ÚNICAMENTE con un JSON con esta estructura (sin texto extra):\n"
    "{\n"
    '  "assessment": "Evaluación general del código en 2-3 oraciones en español",\n'
    '  "findings": [\n'
    "    {\n"
    '      "severity": "critical" | "warning" | "suggestion",\n'
    '      "category": "Seguridad" | "Clean Code" | "Complejidad",\n'
    '      "line": <número de línea entero>,\n'
    '      "message": "Descripción del problema en español",\n'
    '      "suggestion": "Cómo corregirlo en español"\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Sé preciso con los números de línea. Reporta solo problemas reales y concretos."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "assessment": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["critical", "warning", "suggestion"]},
                    "category": {"type": "string", "enum": ["Seguridad", "Clean Code", "Complejidad"]},
                    "line": {"type": "integer"},
                    "message": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
                "required": ["severity", "category", "line", "message", "suggestion"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["assessment", "findings"],
    "additionalProperties": False,
}


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY no está configurada")
        _client = anthropic.AsyncAnthropic(api_key=api_key)
    return _client


async def analyze_with_llm(code: str, file_path: Path) -> tuple[list[Finding], str]:
    """Retorna (findings, assessment). Nunca lanza excepción — falla silenciosamente."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return [], ""

    try:
        client = _get_client()

        response = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2048,
            system=_SYSTEM,
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": _SCHEMA,
                }
            },
            messages=[
                {
                    "role": "user",
                    "content": f"Archivo: `{file_path.name}`\n\n```\n{code}\n```",
                }
            ],
        )

        text = next(b.text for b in response.content if b.type == "text")
        data = json.loads(text)

        findings = [
            Finding(
                severity=f["severity"],
                category=f["category"],
                line=f.get("line", 0),
                message=f["message"],
                suggestion=f["suggestion"],
            )
            for f in data.get("findings", [])
        ]

        return findings, data.get("assessment", "")

    except Exception:
        return [], ""

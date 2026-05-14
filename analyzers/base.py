from dataclasses import dataclass


@dataclass
class Finding:
    severity: str   # "critical" | "warning" | "suggestion"
    category: str   # "Seguridad" | "Clean Code" | "Complejidad"
    line: int
    message: str
    suggestion: str

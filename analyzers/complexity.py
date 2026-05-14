import ast
import re
from pathlib import Path
from .base import Finding

_CC_CRITICAL = 10
_CC_WARNING = 5
_NESTING_CRITICAL = 5
_NESTING_WARNING = 3


def analyze_complexity(code: str, file_path: Path) -> list[Finding]:
    if file_path.suffix == ".py":
        return _analyze_python(code)
    return _analyze_generic(code)


# ─── Python (AST) ────────────────────────────────────────────────────────────

def _analyze_python(code: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(code)
        visitor = _PythonComplexityVisitor()
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError:
        pass
    return findings


class _PythonComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        cc = _cyclomatic_complexity(node)
        depth = _max_nesting_depth(node)

        if cc > _CC_CRITICAL:
            self.findings.append(Finding(
                severity="critical",
                category="Complejidad",
                line=node.lineno,
                message=f"Función '{node.name}' tiene complejidad ciclomática {cc} (máximo: {_CC_CRITICAL})",
                suggestion="Refactorizar: extraer ramas lógicas, usar polimorfismo o early return",
            ))
        elif cc > _CC_WARNING:
            self.findings.append(Finding(
                severity="warning",
                category="Complejidad",
                line=node.lineno,
                message=f"Función '{node.name}' tiene complejidad ciclomática {cc} (recomendado: ≤{_CC_WARNING})",
                suggestion="Considerar dividir la función o simplificar las condiciones compuestas",
            ))

        if depth > _NESTING_CRITICAL:
            self.findings.append(Finding(
                severity="critical",
                category="Complejidad",
                line=node.lineno,
                message=f"Función '{node.name}' tiene {depth} niveles de anidamiento (máximo: {_NESTING_CRITICAL})",
                suggestion="Aplicar early return / guard clauses para invertir las condiciones y reducir el anidamiento",
            ))
        elif depth > _NESTING_WARNING:
            self.findings.append(Finding(
                severity="warning",
                category="Complejidad",
                line=node.lineno,
                message=f"Función '{node.name}' tiene {depth} niveles de anidamiento (recomendado: ≤{_NESTING_WARNING})",
                suggestion="Extraer bloques internos en funciones auxiliares con nombres descriptivos",
            ))

        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]


def _cyclomatic_complexity(node: ast.FunctionDef) -> int:
    count = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
        elif isinstance(child, ast.comprehension) and child.ifs:
            count += len(child.ifs)
    return count


def _max_nesting_depth(root: ast.AST) -> int:
    _block_types = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)

    def _depth(node: ast.AST, current: int) -> int:
        max_d = current
        for child in ast.iter_child_nodes(node):
            next_level = current + 1 if isinstance(child, _block_types) else current
            max_d = max(max_d, _depth(child, next_level))
        return max_d

    return _depth(root, 0)


# ─── Generic JS / TS / Java (regex) ──────────────────────────────────────────

_BRANCH_RE = re.compile(r"\b(if|else\s+if|for|while|switch|catch)\b|&&|\|\|")
_FUNC_RE = re.compile(r"\bfunction\s+(\w+)\s*\(")


def _analyze_generic(code: str) -> list[Finding]:
    findings: list[Finding] = []
    for func_name, start_line, body in _extract_js_functions(code):
        cc = _count_js_cc(body)
        if cc > _CC_CRITICAL:
            findings.append(Finding(
                severity="critical",
                category="Complejidad",
                line=start_line,
                message=f"Función '{func_name}' tiene complejidad ciclomática ~{cc} (máximo: {_CC_CRITICAL})",
                suggestion="Refactorizar: extraer ramas lógicas, reducir condiciones compuestas",
            ))
        elif cc > _CC_WARNING:
            findings.append(Finding(
                severity="warning",
                category="Complejidad",
                line=start_line,
                message=f"Función '{func_name}' tiene complejidad ciclomática ~{cc} (recomendado: ≤{_CC_WARNING})",
                suggestion="Considerar dividir la función o extraer condiciones en variables con nombre descriptivo",
            ))
    return findings


def _extract_js_functions(code: str) -> list[tuple[str, int, str]]:
    results: list[tuple[str, int, str]] = []
    for match in _FUNC_RE.finditer(code):
        func_name = match.group(1)
        start_line = code[: match.start()].count("\n") + 1
        brace_start = code.find("{", match.end())
        if brace_start == -1:
            continue
        depth = 0
        for i in range(brace_start, len(code)):
            if code[i] == "{":
                depth += 1
            elif code[i] == "}":
                depth -= 1
                if depth == 0:
                    results.append((func_name, start_line, code[brace_start: i + 1]))
                    break
    return results


def _count_js_cc(body: str) -> int:
    return 1 + len(_BRANCH_RE.findall(body))

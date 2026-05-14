import ast
import re
from pathlib import Path
from .base import Finding

_MAX_LINES_WARNING = 20
_MAX_LINES_CRITICAL = 35
_SHORT_NAME_EXCEPTIONS = frozenset({"_"})
_SHORT_VAR_PATTERN = re.compile(r"\b(?:var|let|const)\s+([a-zA-Z])\s*[=;,\)]")


def analyze_clean_code(code: str, file_path: Path) -> list[Finding]:
    if file_path.suffix == ".py":
        return _analyze_python(code)
    return _analyze_generic(code)


# ─── Python (AST) ────────────────────────────────────────────────────────────

def _analyze_python(code: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(code)
        visitor = _PythonCleanCodeVisitor()
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError:
        pass
    return findings


class _PythonCleanCodeVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function_length(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Assign(self, node: ast.Assign) -> None:
        self._check_short_names(node)
        self.generic_visit(node)

    def _check_function_length(self, node: ast.FunctionDef) -> None:
        if not node.end_lineno:
            return
        length = node.end_lineno - node.lineno + 1
        if length > _MAX_LINES_CRITICAL:
            self.findings.append(Finding(
                severity="critical",
                category="Clean Code",
                line=node.lineno,
                message=f"Función '{node.name}' tiene {length} líneas (máximo recomendado: {_MAX_LINES_WARNING})",
                suggestion="Dividir en funciones más pequeñas con responsabilidad única (SRP)",
            ))
        elif length > _MAX_LINES_WARNING:
            self.findings.append(Finding(
                severity="warning",
                category="Clean Code",
                line=node.lineno,
                message=f"Función '{node.name}' tiene {length} líneas (máximo recomendado: {_MAX_LINES_WARNING})",
                suggestion="Extraer lógica repetida o compleja en funciones auxiliares",
            ))

    def _check_short_names(self, node: ast.Assign) -> None:
        for target in node.targets:
            for name, lineno in _collect_names(target):
                if len(name) == 1 and name not in _SHORT_NAME_EXCEPTIONS:
                    self.findings.append(Finding(
                        severity="suggestion",
                        category="Clean Code",
                        line=lineno,
                        message=f"Variable '{name}' tiene nombre poco descriptivo (1 caracter)",
                        suggestion="Usar un nombre que describa su propósito: 'user_count', 'total_price'",
                    ))


def _collect_names(node: ast.expr) -> list[tuple[str, int]]:
    if isinstance(node, ast.Name):
        return [(node.id, node.lineno)]
    if isinstance(node, (ast.Tuple, ast.List)):
        result: list[tuple[str, int]] = []
        for elt in node.elts:
            result.extend(_collect_names(elt))
        return result
    return []


# ─── Generic JS / TS / Java (regex) ──────────────────────────────────────────

_TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)


def _analyze_generic(code: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = code.splitlines()

    findings.extend(_check_js_function_length(lines))

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        match = _SHORT_VAR_PATTERN.search(stripped)
        if match:
            var_name = match.group(1)
            if var_name not in _SHORT_NAME_EXCEPTIONS:
                findings.append(Finding(
                    severity="suggestion",
                    category="Clean Code",
                    line=i,
                    message=f"Variable '{var_name}' tiene nombre de 1 caracter (poco descriptivo)",
                    suggestion="Usar un nombre que describa su propósito: 'userCount', 'totalPrice'",
                ))

        if _TODO_PATTERN.search(stripped):
            findings.append(Finding(
                severity="suggestion",
                category="Clean Code",
                line=i,
                message="Comentario pendiente encontrado en el código",
                suggestion="Resolver antes del merge o abrir un issue en el tracker del proyecto",
            ))

    return findings


def _check_js_function_length(lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    func_pattern = re.compile(r"\bfunction\s+(\w+)\s*\(")

    i = 0
    while i < len(lines):
        match = func_pattern.search(lines[i])
        if match:
            func_name = match.group(1)
            start_line = i + 1
            brace_count = 0
            func_started = False

            for j in range(i, len(lines)):
                for ch in lines[j]:
                    if ch == "{":
                        brace_count += 1
                        func_started = True
                    elif ch == "}":
                        brace_count -= 1
                if func_started and brace_count == 0:
                    length = j - i + 1
                    if length > _MAX_LINES_CRITICAL:
                        findings.append(Finding(
                            severity="critical",
                            category="Clean Code",
                            line=start_line,
                            message=f"Función '{func_name}' tiene {length} líneas (máximo: {_MAX_LINES_WARNING})",
                            suggestion="Dividir en funciones más pequeñas con responsabilidad única (SRP)",
                        ))
                    elif length > _MAX_LINES_WARNING:
                        findings.append(Finding(
                            severity="warning",
                            category="Clean Code",
                            line=start_line,
                            message=f"Función '{func_name}' tiene {length} líneas (máximo: {_MAX_LINES_WARNING})",
                            suggestion="Extraer lógica compleja en funciones auxiliares con nombres descriptivos",
                        ))
                    i = j
                    break
        i += 1

    return findings

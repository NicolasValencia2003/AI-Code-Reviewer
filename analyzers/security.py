import ast
import re
from pathlib import Path
from .base import Finding

_SQL_PATTERN = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b", re.IGNORECASE)
_CRED_KEYWORDS = frozenset({
    "password", "passwd", "secret", "api_key", "apikey",
    "token", "private_key", "auth_key", "access_key",
})


def analyze_security(code: str, file_path: Path) -> list[Finding]:
    if file_path.suffix == ".py":
        return _analyze_python(code)
    return _analyze_generic(code)


# ─── Python (AST) ────────────────────────────────────────────────────────────

def _analyze_python(code: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(code)
        visitor = _PythonSecurityVisitor()
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError:
        pass
    return findings


class _PythonSecurityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def visit_Call(self, node: ast.Call) -> None:
        self._check_eval(node)
        self._check_command_injection(node)
        self._check_sql_injection(node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._check_hardcoded_creds(node)
        self.generic_visit(node)

    def _check_eval(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            self.findings.append(Finding(
                severity="critical",
                category="Seguridad",
                line=node.lineno,
                message="eval() detectado — permite ejecución de código arbitrario",
                suggestion="Reemplazar con ast.literal_eval() o lógica explícita sin eval()",
            ))

    def _check_command_injection(self, node: ast.Call) -> None:
        func = node.func
        is_os_shell = (
            isinstance(func, ast.Attribute)
            and func.attr in ("system", "popen")
            and isinstance(func.value, ast.Name)
            and func.value.id == "os"
        )
        is_subprocess_shell = (
            isinstance(func, ast.Attribute)
            and func.attr in ("run", "call", "check_output", "Popen")
            and any(
                kw.arg == "shell"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
                for kw in node.keywords
            )
        )
        if (is_os_shell or is_subprocess_shell) and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, (ast.BinOp, ast.JoinedStr, ast.Name)):
                self.findings.append(Finding(
                    severity="critical",
                    category="Seguridad",
                    line=node.lineno,
                    message="Command injection: shell ejecutado con argumento dinámico",
                    suggestion="Usar subprocess.run() con lista de argumentos y sin shell=True",
                ))

    def _check_sql_injection(self, node: ast.Call) -> None:
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr in ("execute", "executemany", "raw", "query")):
            return
        for arg in node.args:
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                self.findings.append(Finding(
                    severity="critical",
                    category="Seguridad",
                    line=node.lineno,
                    message="SQL Injection: query construida por concatenación de strings",
                    suggestion="Usar parámetros: cursor.execute('SELECT * WHERE id = ?', (uid,))",
                ))
            elif isinstance(arg, ast.JoinedStr) and _SQL_PATTERN.search(_fstring_static_parts(arg)):
                self.findings.append(Finding(
                    severity="critical",
                    category="Seguridad",
                    line=node.lineno,
                    message="SQL Injection: f-string con variables en query SQL",
                    suggestion="Usar parámetros: cursor.execute('SELECT * WHERE id = ?', (uid,))",
                ))

    def _check_hardcoded_creds(self, node: ast.Assign) -> None:
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if not any(kw in target.id.lower() for kw in _CRED_KEYWORDS):
                continue
            if (
                isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and len(node.value.value) > 3
            ):
                self.findings.append(Finding(
                    severity="critical",
                    category="Seguridad",
                    line=node.lineno,
                    message=f"Credencial hardcodeada: '{target.id}' asignada con valor literal",
                    suggestion="Mover a variable de entorno: os.environ.get('SECRET_KEY')",
                ))


def _fstring_static_parts(node: ast.JoinedStr) -> str:
    parts = []
    for value in node.values:
        if isinstance(value, ast.Constant):
            parts.append(str(value.value))
        else:
            parts.append("{}")
    return "".join(parts)


# ─── Generic JS / TS / Java (regex) ──────────────────────────────────────────

_GENERIC_RULES: list[tuple[re.Pattern, str, str, str]] = [
    (
        re.compile(r"\beval\s*\(", re.IGNORECASE),
        "critical",
        "eval() detectado — permite ejecución de código arbitrario",
        "Reemplazar con JSON.parse() o lógica explícita sin eval()",
    ),
    (
        re.compile(r"(SELECT|INSERT|UPDATE|DELETE)\b.*\+\s*\w", re.IGNORECASE),
        "critical",
        "SQL Injection: query SQL construida con concatenación de strings",
        "Usar prepared statements: db.query('SELECT ... WHERE id = ?', [id])",
    ),
    (
        re.compile(r"`\s*(SELECT|INSERT|UPDATE|DELETE)\b.*\$\{", re.IGNORECASE),
        "critical",
        "SQL Injection: template literal con variables en query SQL",
        "Usar prepared statements: db.query('SELECT ... WHERE id = ?', [id])",
    ),
    (
        re.compile(
            r"(password|passwd|secret|api_?key|token|private_?key)\s*[=:]\s*['\"][^'\"]{4,}",
            re.IGNORECASE,
        ),
        "critical",
        "Credencial hardcodeada en el código",
        "Mover a variables de entorno y leer con process.env.VAR_NAME",
    ),
    (
        re.compile(r"\.innerHTML\s*\+?=\s*[^'\"`\n;]{0,5}[^'\"`\n;]"),
        "critical",
        "XSS potencial: asignación dinámica a innerHTML",
        "Usar textContent o sanitizar con DOMPurify antes de asignar a innerHTML",
    ),
    (
        re.compile(r"document\.write\s*\("),
        "warning",
        "document.write() puede sobreescribir el DOM completo",
        "Usar createElement + appendChild en lugar de document.write()",
    ),
]


def _analyze_generic(code: str) -> list[Finding]:
    findings: list[Finding] = []
    for i, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern, severity, message, suggestion in _GENERIC_RULES:
            if pattern.search(stripped):
                findings.append(Finding(
                    severity=severity,
                    category="Seguridad",
                    line=i,
                    message=message,
                    suggestion=suggestion,
                ))
    return findings

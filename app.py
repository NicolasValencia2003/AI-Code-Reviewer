"""AI Code Reviewer — Servidor web (FastAPI)."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from analyzers import analyze_clean_code, analyze_complexity, analyze_security, analyze_with_llm
from analyzers.base import Finding

load_dotenv()

_SUPPORTED = {".py", ".js", ".ts", ".java"}
_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2}
_HTML = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")

app = FastAPI(title="AI Code Reviewer", docs_url=None, redoc_url=None)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _HTML


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    file_path = Path(file.filename)
    if file_path.suffix not in _SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión '{file_path.suffix}' no soportada. Usa: {', '.join(sorted(_SUPPORTED))}",
        )

    code = (await file.read()).decode("utf-8", errors="replace")

    static_findings: list[Finding] = [
        *analyze_security(code, file_path),
        *analyze_clean_code(code, file_path),
        *analyze_complexity(code, file_path),
    ]

    llm_findings, llm_assessment = await analyze_with_llm(code, file_path)

    all_findings = static_findings + llm_findings
    all_findings.sort(key=lambda f: (_SEVERITY_ORDER.get(f.severity, 3), f.line))

    return {
        "filename": file.filename,
        "llm_assessment": llm_assessment,
        "findings": [
            {
                "severity": f.severity,
                "category": f.category,
                "line": f.line,
                "message": f.message,
                "suggestion": f.suggestion,
            }
            for f in all_findings
        ],
        "summary": {
            "critical": sum(1 for f in all_findings if f.severity == "critical"),
            "warning": sum(1 for f in all_findings if f.severity == "warning"),
            "suggestion": sum(1 for f in all_findings if f.severity == "suggestion"),
        },
    }

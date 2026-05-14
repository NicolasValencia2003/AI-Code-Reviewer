# ARQUITECTURA.md — AI Code Reviewer

## Entrypoints

La herramienta tiene dos modos de uso con orquestadores distintos:

| Entrypoint | Cómo se lanza | Análisis |
|------------|---------------|---------|
| `app.py` | `uvicorn app:app --reload` | Estático + LLM (Claude) |
| `reviewer.py` | `python reviewer.py archivo.py` | Solo estático |

---

## Diagrama — Modo Web (`app.py`)

```
 [Navegador — drag & drop]
        │
        │  POST /analyze  (multipart/form-data)
        ▼
 ┌──────────────────────────────────────────┐
 │  app.py  (FastAPI — async)               │
 │  · Valida extensión (.py/.js/.ts/.java)  │
 │  · Decodifica el archivo subido          │
 │  · Lanza analyzers estáticos + LLM       │
 │  · Fusiona y ordena findings             │
 │  · Retorna JSON                          │
 └───────┬──────────────────────────────────┘
         │
    ┌────┴────────────────────────────────────┐
    │ Análisis en paralelo (await asyncio)    │
    ├─────────────┬───────────┬───────────────┤
    ▼             ▼           ▼               ▼
[security]  [clean_code] [complexity]    [llm.py]
    │             │           │               │
    │   list[Finding]         │      Claude claude-opus-4-7
    └─────────────┴───────────┘               │
              │  findings estáticos           │  findings + assessment
              └────────────────┬──────────────┘
                               ▼
                    all_findings ordenados
                    (critical → warning → suggestion)
                               │
                               ▼
              ┌────────────────────────────────┐
              │  JSON Response                 │
              │  { findings, llm_assessment,   │
              │    summary }                   │
              └────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │  templates/index.html          │
              │  · Tabla de hallazgos          │
              │  · Banner 🤖 con assessment    │
              │  · Badges por severidad        │
              └────────────────────────────────┘
```

## Diagrama — Modo CLI (`reviewer.py`)

```
 [Terminal]
        │
        │  python reviewer.py archivo.py archivo.js
        ▼
 ┌─────────────────────────────────┐
 │  reviewer.py  (Typer — síncrono)│
 │  · Valida existencia y extensión│
 │  · Lee archivo como texto       │
 │  · Llama a los 3 analyzers      │
 │  · Fusiona y ordena findings    │
 │  · Envía al reporter            │
 └────────────┬────────────────────┘
              │
     ┌────────┼────────────────┐
     ▼        ▼                ▼
 [security] [clean_code] [complexity]
     │        │                │
     └────────┴────────────────┘
              │  list[Finding] unificada
              ▼
      ┌───────────────┐
      │ reporters/    │
      │ console.py    │
      │ (Rich table)  │
      └───────────────┘
              │
              ▼
    [Tabla con colores en terminal]
    🔴 CRÍTICO | 🟡 ADVERT. | 🟢 SUGER.
```

---

## Capas del Sistema

### Capa de Entrada Web (`app.py`)
- Servidor FastAPI con endpoint `POST /analyze` y `GET /` (sirve el HTML)
- Recibe archivos vía `multipart/form-data`
- Valida extensión; retorna HTTP 400 si no es soportada
- Decodifica bytes con `errors="replace"` (sin crashear por encodings raros)
- Llama a los 3 analyzers estáticos + `analyze_with_llm` (todos async-compatible)
- Ordena findings: `critical → warning → suggestion`, luego por línea
- Retorna JSON con `findings`, `llm_assessment` y `summary`

### Capa de Entrada CLI (`reviewer.py`)
- Typer CLI — acepta uno o más paths como argumentos posicionales
- Valida existencia del archivo y extensión soportada
- Lee contenido UTF-8, llama a los 3 analyzers estáticos (sin LLM)
- Pasa findings a `reporters/console.py`

### Capa de Análisis Estático (`analyzers/`)
Tres módulos independientes, cada uno retorna `list[Finding]`:

| Módulo | Qué detecta | Motor |
|--------|-------------|-------|
| `security.py` | SQL Injection, credenciales hardcodeadas, `eval()`, command injection, XSS | AST (Python) / Regex (JS/TS/Java) |
| `clean_code.py` | Funciones >20 líneas, variables de 1 caracter, TODO/FIXME pendientes | AST (Python) / Regex (JS/TS/Java) |
| `complexity.py` | Complejidad ciclomática (>10 crítico, >5 advertencia), anidamiento >5 niveles | AST (Python) / Regex (JS/TS/Java) |

Para **Python** se usa el módulo `ast` — analiza el árbol sintáctico y detecta estructuras exactas (f-strings en SQL, BoolOp anidados, etc.).  
Para **JS/TS/Java** se usa regex línea a línea — cubre los patrones más comunes sin dependencias externas.

### Capa de Análisis Semántico (`analyzers/llm.py`)
- Llama a Claude (`claude-opus-4-7`) via Anthropic SDK async
- Usa `output_config.format.json_schema` para garantizar JSON estructurado sin parseo libre
- Retorna `(list[Finding], str)` — findings + evaluación general en lenguaje natural
- **Nunca lanza excepción hacia afuera** — retorna `([], "")` ante cualquier error
- Si `ANTHROPIC_API_KEY` no está configurada, retorna `([], "")` inmediatamente (degradación graceful)

### Capa de Datos (`analyzers/base.py`)
Único tipo de dato que fluye entre capas:

```python
@dataclass
class Finding:
    severity: str    # "critical" | "warning" | "suggestion"
    category: str    # "Seguridad" | "Clean Code" | "Complejidad"
    line: int        # Número de línea en el archivo original
    message: str     # Descripción del problema detectado
    suggestion: str  # Cómo corregirlo
```

### Capa de Presentación Web (`templates/index.html`)
- HTML + Tailwind CSS (CDN) + JavaScript vanilla
- Drag & drop de archivos, llamada fetch al endpoint `/analyze`
- Renderiza tabla de hallazgos con badges de severidad (🔴 / 🟡 / 🟢)
- Muestra banner 🤖 con la evaluación general de Claude cuando está disponible

### Capa de Presentación CLI (`reporters/console.py`)
- Recibe `list[Finding]` ya ordenada
- Renderiza con Rich: tabla con colores por severidad, bordes redondeados
- Imprime resumen: total de críticos, advertencias y sugerencias

---

## Decisiones Técnicas

| Decisión | Justificación |
|----------|---------------|
| FastAPI (no Flask) | Soporte nativo `async/await` — no bloquea el servidor durante la llamada al LLM |
| `claude-opus-4-7` con `json_schema` | Garantiza JSON válido con el schema esperado sin parsear texto libre; elimina errores de formato |
| Degradación graceful del LLM | Si no hay API key o Claude falla, `analyze_with_llm` retorna `([], "")` — la demo nunca crashea |
| Python AST para `.py` | Detecta estructuras exactas (f-strings en SQL, concatenaciones). Regex produciría falsos positivos |
| Regex para JS/TS/Java | No hay parser AST de estos lenguajes en la stdlib de Python. Regex cubre el 90% de casos sin dependencias pesadas |
| Dos entrypoints separados | `app.py` (web + LLM) y `reviewer.py` (CLI sin LLM) — cada modo tiene su orquestador propio, sin acoplar el reporter de terminal con la API REST |
| `python-dotenv` | Carga `ANTHROPIC_API_KEY` desde `.env` sin exponer la key en el código o en el historial de shell |
| Typer (no Click/argparse) | API moderna con type hints, genera ayuda automática, menos boilerplate |
| Rich (no tabulate/print) | Tablas con colores en terminal, estándar de facto para CLIs modernas en Python |
| Dataclass `Finding` | Estructura tipada compartida entre todos los módulos. Permite que analyzers y reporters sean intercambiables |
| Falsos negativos > falsos positivos | Una herramienta que genera ruido pierde la confianza del equipo |

---

## Dependencias

| Librería | Versión | Para qué |
|----------|---------|----------|
| `fastapi` | ≥0.110.0 | Servidor web async y endpoint REST `/analyze` |
| `uvicorn` | ≥0.27.0 | Servidor ASGI para FastAPI |
| `python-multipart` | ≥0.0.9 | Parsing de `multipart/form-data` (subida de archivos) |
| `anthropic` | ≥0.52.0 | SDK oficial de Anthropic — llamadas a Claude |
| `python-dotenv` | ≥1.0.0 | Carga de `ANTHROPIC_API_KEY` desde `.env` |
| `typer` | ≥0.12.0 | CLI con type hints y generación automática de ayuda |
| `rich` | ≥13.7.0 | Output con tablas y colores en terminal |
| `ast` | stdlib (3.8+) | Análisis sintáctico de código Python |
| `re` | stdlib | Análisis por expresiones regulares para JS/TS/Java |
| `dataclasses` | stdlib (3.7+) | Definición del tipo `Finding` |

---

*Mantén este documento actualizado conforme evoluciona el proyecto.*

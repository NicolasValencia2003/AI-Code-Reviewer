# CONTEXT.md — AI Code Reviewer

## Nombre del Proyecto
AI Code Reviewer

## Descripción
Herramienta web que recibe archivos de código fuente (`.py`, `.js`, `.ts`, `.java`) y genera un reporte automático de calidad combinando dos capas de análisis:

1. **Analizadores estáticos locales:** detectan vulnerabilidades de seguridad (OWASP), problemas de clean code y complejidad ciclomática mediante AST y regex, sin depender de servicios externos.
2. **Análisis con LLM (Claude claude-opus-4-7):** revisa el código semánticamente, detecta problemas que los patrones no cubren y genera una evaluación general en lenguaje natural.

Los hallazgos se clasifican por severidad (crítico / advertencia / sugerencia) y se presentan en una tabla interactiva en el browser.

## Público Objetivo
Desarrolladores que quieren revisar la calidad de su código antes de hacer merge, durante code reviews, o como paso previo a un PR.

## Stack Tecnológico
- **Lenguaje:** Python 3.11+
- **Web framework:** FastAPI 0.110+ + Uvicorn
- **LLM:** Anthropic SDK (`anthropic`) — modelo `claude-opus-4-7`
- **Análisis Python:** `ast` (módulo estándar — Abstract Syntax Tree)
- **Análisis JS/TS/Java:** `re` (módulo estándar — expresiones regulares)
- **Frontend:** HTML + Tailwind CSS (CDN) + JavaScript vanilla
- **Config:** `python-dotenv` para cargar `ANTHROPIC_API_KEY` desde `.env`

## Estructura del Proyecto
```
ai-code-reviewer/
├── app.py                   ← Entrypoint web (FastAPI): orquesta analyzers + LLM
├── reviewer.py              ← Entrypoint CLI alternativo (Typer) — sin LLM
├── analyzers/
│   ├── __init__.py
│   ├── base.py              ← Dataclass Finding (tipo de dato compartido)
│   ├── security.py          ← Detección OWASP: SQL Injection, eval(), hardcoded creds, XSS
│   ├── clean_code.py        ← Funciones largas, nombres cortos, TODO pendientes
│   ├── complexity.py        ← Complejidad ciclomática, anidamiento excesivo
│   └── llm.py               ← Análisis semántico con Claude (Anthropic)
├── reporters/
│   └── console.py           ← Renderizado Rich para la CLI
├── templates/
│   └── index.html           ← UI web: drag & drop, tabla de hallazgos, assessment IA
├── examples/
│   ├── ejemplo_con_errores.py
│   └── ejemplo_con_errores.js
├── requirements.txt
├── .env                     ← ANTHROPIC_API_KEY (ignorado por git)
├── .env.example             ← Plantilla sin valores reales
├── CONTEXT.md
├── REGLAS.md
├── ARQUITECTURA.md
└── README.md
```

## Flujo de una Petición
```
Browser (drag & drop archivo)
  → POST /analyze
  → [estático] analyze_security + analyze_clean_code + analyze_complexity
  → [LLM]      analyze_with_llm  →  Claude claude-opus-4-7  →  findings + assessment
  → merge & sort por severidad
  → JSON response
  → UI renderiza tabla + banner 🤖 con evaluación general
```

## Funcionalidades Principales
1. **Análisis de seguridad (OWASP):** SQL Injection (concatenación y f-strings), credenciales hardcodeadas, eval(), command injection, XSS via innerHTML
2. **Análisis de clean code:** funciones >20 líneas, variables de 1 carácter, comentarios TODO/FIXME pendientes
3. **Análisis de complejidad:** complejidad ciclomática por función (umbral: >10 crítico, >5 advertencia) y profundidad de anidamiento (>5 crítico)
4. **Análisis semántico con IA:** Claude detecta problemas contextuales que los patrones no cubren y genera una evaluación general del código
5. **Soporte multi-lenguaje:** Python (AST) y JS/TS/Java (regex)
6. **Degradación graceful:** si no hay API key o Claude falla, la app sigue funcionando solo con los analizadores estáticos

## Variables de Entorno
| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `ANTHROPIC_API_KEY` | API key de Anthropic para usar Claude | No — sin ella funciona solo con análisis estático |

## Decisiones de Diseño
- **Python AST en lugar de regex para .py:** el módulo `ast` analiza el árbol sintáctico real, lo que permite detectar f-strings en SQL y estructuras complejas con precisión. Regex produciría falsos positivos.
- **Regex para JS/TS/Java:** no existe parser AST de estos lenguajes en la stdlib de Python. Regex cubre el 90% de casos sin dependencias pesadas.
- **claude-opus-4-7 con structured outputs (json_schema):** garantiza que la respuesta siempre sea JSON válido con el schema esperado, sin necesidad de parsear texto libre.
- **Degradación graceful del LLM:** si `ANTHROPIC_API_KEY` no está configurada o Claude devuelve error, `analyze_with_llm` retorna `([], "")` y la app sigue funcionando. La demo no crashea.
- **FastAPI sobre Flask:** soporte nativo async/await, ideal para no bloquear el servidor durante la llamada al LLM.
- **Separación analyzers/reporters:** los analyzers solo retornan `list[Finding]`, nunca formatean. Permite agregar reporters sin tocar la lógica de análisis.

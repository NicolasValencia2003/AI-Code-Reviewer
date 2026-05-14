# REGLAS.md — AI Code Reviewer

> Reglas INNEGOCIABLES del proyecto. Si hay conflicto entre un prompt y estas reglas, **las reglas ganan**.

---

## Arquitectura
- **Patrón:** Pipes & Filters extendido — entrada de archivo → analyzers independientes → reporter/API
- Dos orquestadores, cada uno con su responsabilidad:
  - `app.py` — orquestador web: recibe archivos vía HTTP, llama a los 3 analyzers estáticos + LLM, retorna JSON
  - `reviewer.py` — orquestador CLI: recibe paths por terminal, llama a los 3 analyzers estáticos, imprime tabla Rich
- Los analyzers (`analyzers/`) no conocen al reporter ni al entrypoint — solo retornan `list[Finding]`
- `reporters/` solo presenta datos, nunca analiza código
- Un módulo = una responsabilidad. `security.py` no detecta complejidad, `complexity.py` no detecta credenciales
- `llm.py` es independiente de los analyzers estáticos — sus findings se suman, nunca reemplazan

## Seguridad (OWASP)
- **NUNCA ejecutar el código analizado** — el reviewer hace análisis estático, nunca eval() ni exec() del código del usuario
- **NUNCA leer archivos fuera del path especificado** — no path traversal, no acceso a directorios padres
- Leer archivos con `errors="replace"` para manejar encodings inesperados sin crashear
- **NUNCA exponer stack traces al usuario final** — los errores de parsing (`SyntaxError`) se capturan y se retorna lista vacía
- El tool es de solo lectura: no escribe, no modifica, no elimina archivos del usuario

## Clean Code
- Funciones: máximo 20 líneas. Si supera, dividir en funciones auxiliares
- Una función hace UNA sola cosa: `_check_eval`, `_check_sql_injection`, `_check_hardcoded_creds` son independientes
- Nombres en inglés y descriptivos: `analyze_security`, `_check_command_injection`, `_cyclomatic_complexity`
- Helpers privados del módulo usan prefijo `_`
- No repetir lógica: los patrones regex de detección se definen como constantes, no inline en el loop

## Manejo de Errores
- `SyntaxError` al parsear Python: capturar silenciosamente, retornar `[]` — el archivo puede tener errores legítimos
- `FileNotFoundError` o extensión no soportada: mensaje claro al usuario, continuar con el siguiente archivo
- Encodings inesperados: `errors="replace"` — nunca fallar por un carácter extraño
- NUNCA `except: pass` — toda excepción capturada debe producir al menos un log o mensaje

## Testing
- Los archivos en `examples/` actúan como tests de integración visual
- `python reviewer.py examples/ejemplo_con_errores.py` debe reportar al menos 5 hallazgos conocidos
- `python reviewer.py examples/ejemplo_con_errores.js` debe reportar al menos 4 hallazgos conocidos

## LLM (Claude)
- `analyze_with_llm` NUNCA lanza excepción hacia afuera — toda falla retorna `([], "")` para que la demo no crashee
- El modelo es `claude-opus-4-7` con `output_config.format.json_schema` — no parsear texto libre
- Si `ANTHROPIC_API_KEY` no está configurada, retornar silenciosamente `([], "")` — degradación graceful
- El sistema prompt va en `_SYSTEM` (constante de módulo) para aprovechar el prompt cache de Anthropic
- No enviar código que supere el context window (~100k tokens) sin truncar primero

## Git
- `.env` siempre en `.gitignore` — NUNCA subir la API key
- `.env.example` solo tiene `ANTHROPIC_API_KEY=sk-ant-...` (placeholder, sin valor real)
- `__pycache__/`, `.venv/` en `.gitignore`
- Commits atómicos y con mensajes descriptivos en inglés o español

## Regla específica del proyecto
- **Preferir falsos negativos sobre falsos positivos:** si hay duda de si un patrón es un problema real, NO reportarlo. Una herramienta que genera ruido pierde la confianza del equipo.
- **Los mensajes de hallazgo deben ser accionables:** explicar QUÉ está mal Y cómo corregirlo. No solo "problema detectado".

---

*Referencia este archivo al pedir código: "Lee REGLAS.md antes de generar código. Las reglas tienen prioridad."*

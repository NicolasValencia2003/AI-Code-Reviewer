# AI Code Reviewer

Herramienta de revisión de código que combina **análisis estático** y **análisis semántico con IA** para detectar vulnerabilidades de seguridad, problemas de clean code y complejidad ciclomática en archivos `.py`, `.js`, `.ts` y `.java`.

Disponible como **app web** (drag & drop en el navegador) y como **CLI** en la terminal.

> Proyecto Final — IA for Devs · Universidad Javeriana Cali 2026-1

---

## Cómo funciona

Cada archivo pasa por dos capas de análisis en paralelo:

```
Archivo subido
  ├── Analizadores estáticos (locales, sin internet)
  │     ├── security.py   → SQL Injection, eval(), credenciales, XSS, command injection
  │     ├── clean_code.py → Funciones largas, nombres poco descriptivos, TODO pendientes
  │     └── complexity.py → Complejidad ciclomática, anidamiento excesivo
  │
  └── Claude claude-opus-4-7 (Anthropic)
        → Análisis semántico: detecta problemas contextuales que los patrones no cubren
        → Evaluación general del código en lenguaje natural
  
  → Resultados combinados, ordenados por severidad
```

Si no hay API key configurada, la app funciona igual usando solo los analizadores estáticos.

---

## Instalación

**Requisitos:** Python 3.11+

```bash
# 1. Clonar el repositorio
git clone https://github.com/NicolasValencia2003/ai-code-reviewer.git
cd ai-code-reviewer

# 2. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### Configurar la API key de Anthropic (opcional)

Para habilitar el análisis con Claude, crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
# Edita .env y pega tu API key:
# ANTHROPIC_API_KEY=sk-ant-...
```

Obtén tu API key en [console.anthropic.com](https://console.anthropic.com).

---

## Uso

### App web (recomendado)

```bash
uvicorn app:app --reload
```

Abre [http://localhost:8000](http://localhost:8000) en el navegador, arrastra uno o más archivos y haz clic en **Analizar código**.

Cada resultado muestra:
- Banner 🤖 con la evaluación general de Claude
- Tabla de hallazgos ordenada por severidad (crítico → advertencia → sugerencia)
- Número de línea, descripción del problema y sugerencia de corrección

### CLI (terminal)

```bash
# Analizar un archivo
python reviewer.py examples/ejemplo_con_errores.py

# Analizar múltiples archivos
python reviewer.py examples/ejemplo_con_errores.py examples/ejemplo_con_errores.js

# Ver opciones disponibles
python reviewer.py --help
```

Nota: la CLI usa solo los analizadores estáticos (sin LLM).

---

## Ejemplo de output — CLI

```
──────────── 📊 Reporte de Calidad: ejemplo_con_errores.py ────────────
┌─────────────┬──────────────┬───────┬───────────────────────────────────────┬────────────────────────────────────┐
│ Sev.        │ Categoría    │ Línea │ Hallazgo                              │ Sugerencia                         │
├─────────────┼──────────────┼───────┼───────────────────────────────────────┼────────────────────────────────────┤
│ 🔴 CRÍTICO  │ Seguridad    │    12 │ Credencial hardcodeada: 'password'    │ Usar os.environ.get('SECRET_KEY')  │
│ 🔴 CRÍTICO  │ Seguridad    │    21 │ SQL Injection: query concatenada      │ cursor.execute('... WHERE id=?',..)│
│ 🔴 CRÍTICO  │ Seguridad    │    43 │ eval() detectado — código arbitrario  │ Reemplazar con ast.literal_eval()  │
│ 🔴 CRÍTICO  │ Complejidad  │    87 │ Complejidad ciclomática 13 (máx: 10)  │ Extraer ramas en funciones         │
│ 🟡 ADVERT.  │ Complejidad  │    47 │ Anidamiento de 7 niveles (rec: ≤5)    │ Aplicar early return / guard clause│
│ 🟢 SUGER.   │ Clean Code   │    47 │ Variable 'x' poco descriptiva         │ Usar: 'username', 'total_price'    │
└─────────────┴──────────────┴───────┴───────────────────────────────────────┴────────────────────────────────────┘
  Total: 4 crítico(s)  1 advertencia(s)  1 sugerencia(s)
```

---

## Qué detecta

| Categoría | Severidad | Ejemplos |
|-----------|-----------|---------|
| **Seguridad** | 🔴 Crítico | SQL Injection por concatenación o f-string, `eval()`, credenciales hardcodeadas, `os.system()` con argumento dinámico, XSS via `innerHTML` |
| **Clean Code** | 🟡 Advertencia | Funciones de más de 20 líneas, variables de un solo caracter |
| **Clean Code** | 🟢 Sugerencia | Comentarios `TODO` / `FIXME` sin resolver |
| **Complejidad** | 🔴 Crítico | Complejidad ciclomática > 10, anidamiento > 5 niveles |
| **Complejidad** | 🟡 Advertencia | Complejidad ciclomática > 5 |

---

## Lenguajes soportados

| Lenguaje | Extensión | Motor de análisis |
|----------|-----------|-------------------|
| Python | `.py` | AST nativo — análisis estructural del árbol sintáctico |
| JavaScript | `.js` | Regex — detección por patrones línea a línea |
| TypeScript | `.ts` | Regex — detección por patrones línea a línea |
| Java | `.java` | Regex — detección por patrones línea a línea |

Python usa AST porque permite detectar estructuras exactas (f-strings con SQL, concatenaciones en argumentos de `execute()`) sin falsos positivos. Para los demás lenguajes no existe un parser en la stdlib de Python, por lo que se usa regex.

---

## Estructura del proyecto

```
ai-code-reviewer/
├── app.py                    ← Servidor web (FastAPI) — orquesta estático + LLM
├── reviewer.py               ← CLI alternativa (Typer) — solo análisis estático
├── analyzers/
│   ├── base.py               ← Dataclass Finding (tipo de dato compartido)
│   ├── security.py           ← Seguridad OWASP: SQL Injection, eval(), XSS...
│   ├── clean_code.py         ← Clean Code: funciones largas, nombres cortos
│   ├── complexity.py         ← Complejidad ciclomática y anidamiento
│   └── llm.py                ← Análisis semántico con Claude (Anthropic)
├── reporters/
│   └── console.py            ← Output Rich para la CLI
├── templates/
│   └── index.html            ← UI web: drag & drop + tabla de hallazgos
├── examples/
│   ├── ejemplo_con_errores.py
│   └── ejemplo_con_errores.js
├── requirements.txt
├── .env.example              ← Plantilla de variables de entorno
├── CONTEXT.md                ← Contexto completo del proyecto para IA
├── REGLAS.md                 ← Reglas de arquitectura y seguridad
└── ARQUITECTURA.md           ← Diagrama y decisiones técnicas
```

---

## Dependencias

| Librería | Para qué |
|----------|----------|
| `fastapi` + `uvicorn` | Servidor web y API REST |
| `anthropic` | SDK oficial de Anthropic para llamar a Claude |
| `python-dotenv` | Cargar `ANTHROPIC_API_KEY` desde `.env` |
| `typer` | CLI con type hints y generación automática de ayuda |
| `rich` | Tablas con colores en terminal (modo CLI) |

---

## Documentación técnica

- [CONTEXT.md](CONTEXT.md) — Stack, estructura, flujo de datos y decisiones de diseño
- [REGLAS.md](REGLAS.md) — Reglas de arquitectura, seguridad y uso del LLM
- [ARQUITECTURA.md](ARQUITECTURA.md) — Diagrama de capas y decisiones técnicas

---

*IA for Devs · Universidad Javeriana Cali 2026-1*

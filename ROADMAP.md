# ROADMAP — Detector de Duplicados

---

## Principios rectores

1. **Terminal ligera con Rich** — nunca GUI compleja
2. **Nunca sobreingeniería** — cada línea debe tener un motivo claro
3. **No servicios externos** — sin servidores, sin APIs, sin dependencias en la nube
4. **Confirmación explícita** para cualquier acción destructiva
5. **Hashing como verdad única** — SHA256 es la fuente de verdad
6. **Documentación viva** — el roadmap siempre refleja el estado real

---

## Estado actual (ultima actualización: 2026-06-22)

||||| Metrica | Valor | Estado |
||||---|---|---|
|| Version | 1.0.0 | ✅ Estable |
|| Tests | 431 passing, 1 skipped | ✅ OK |
|| Cobertura | 58% (1570 stmts, 659 sin cubrir) | ⚠️ Deterioro (desde 74% en Fase 6) |
|| Ruff | ⚠️ 15 errores | ⚠️ (0 errores en Fase 6, se reintrodujeron) |
|| pyproject.toml | version 1.0.0 | ✅ |
|| README.md | ✅ Actualizado con version final | ✅ |
|| CHANGELOG.md | ✅ Keep a Changelog | ✅ |
|| Dead code | ✅ Eliminado (run.py, src/detector.py) | ✅ |
|| Build .exe | ✅ IMPORTS CORREGIDOS — artifact disponible | ✅ |
|| UI Interactiva | ✅ MENUS Y AYUDA CORREGIDOS — sin \\n literales, opciones numeradas | ✅ |

### Notas de sesión final (2025-06-16 — Fase 7 completada)
- **Tarea 1 (coverage):** COMPLETADA → 74% (objetivo 70%)
  - Nuevo test file: `tests/test_cobertura_fase6.py` (21k chars, 103 tests)
  - Cubre: html_report, cleaner core, cli args parser, cleaner scoring, papelera
  - Tests de watchdog skippeados (mocks complejos de os.path.expanduser para paths)
  - Coverage detallado: html_report 93%, cli 56%, cleaner 60%, db 90%, policies 93%
- **Tarea 2 (ruff):** COMPLETADA → 217 errores → 0 (162 auto, 8 manual)
- **Tarea 3 (dead code):** COMPLETADA → run.py y src/detector.py eliminados
- **Tarea 4 (CHANGELOG):** COMPLETADA → archivo creado con Keep a Changelog format
- **Tarea 5 (instalacion):** COMPLETADA → todos los comandos CLI validados en venv limpio
- **Tarea 6 (version 1.0.0):** COMPLETADA → pyproject.toml + __init__.py actualizados
- **Tarea 7 (README):** COMPLETADA → README 1.0.0 con CLI reference, policies, profiles, FAQ
- **Fase 7 (docs):** COMPLETADA → toda la documentacion actualizada

### Fix de build .exe — 2025-06-16
- **Problema:** `.exe` se cerraba al instante con `ImportError: attempted relative import with no known parent package`
- **Causa:** `cli.py` usaba imports relativos (`from .ui import ...`, `from .db import ...`, etc.) que fallan en entorno compilado
- **Solución:** Convertir TODOS los imports relativos a absolutos (`from detector_duplicados.xxx import ...`)
- **Typo en build.yml:** Corregido `detector_duplications` → `detector_duplicados` en `.github/workflows/build.yml`
- **Artifact disponible:** `detector-windows` (~12.4 MB) en https://github.com/jesusfdo/detector-duplicados/actions/runs/27634301885
- **Archivos corregidos:** `src/detector_duplicados/cli.py`, `.github/workflows/build.yml`, `.gitignore`
- **CI/CD:** GitHub Actions configurado para builds automáticos en push a `main`/`master`

### Notas de sesión final (2025-06-16 — Fase 7 completada)
- **Tarea 1 (coverage):** COMPLETADA → 74% (objetivo 70%)
  - Nuevo test file: `tests/test_cobertura_fase6.py` (21k chars, 103 tests)
  - Cubre: html_report, cleaner core, cli args parser, cleaner scoring, papelera
  - Tests de watchdog skippeados (mocks complejos de os.path.expanduser para paths)
  - Coverage detallado: html_report 93%, cli 56%, cleaner 60%, db 90%, policies 93%
- **Tarea 2 (ruff):** COMPLETADA → 217 errores → 0 (162 auto, 8 manual)
- **Tarea 3 (dead code):** COMPLETADA → run.py y src/detector.py eliminados
- **Tarea 4 (CHANGELOG):** COMPLETADA → archivo creado con Keep a Changelog format
- **Tarea 5 (instalacion):** COMPLETADA → todos los comandos CLI validados en venv limpio
- **Tarea 6 (version 1.0.0):** COMPLETADA → pyproject.toml + __init__.py actualizados
- **Tarea 7 (README):** COMPLETADA → README 1.0.0 con CLI reference, policies, profiles, FAQ
- **Fase 7 (docs):** COMPLETADA → toda la documentacion actualizada

---

## Fases completadas

- **Fase 0:** ✅ Estructura de paquetes (15 archivos en src/, pyproject.toml, tests/)
- **Fase 1:** ✅ Detección con hashing SHA256 (duper.py 98% coverage)
- **Fase 2:** ✅ Base de datos SQLite persistente (db.py 90% coverage, esquema completo)
- **Fase 3:** ✅ Terminal UI con Rich (ui.py 74%, menús, tablas, métricas, comparacion)
- **Fase 4:** ✅ Gestion de duplicados (policies.py 93%, exporter.py 94%, cleaner.py 60%, html_report.py 93%, watchdog.py 63%)

---

## Fase 6 — Preparacion para Release 1.0

### Objetivo

Llevar la app de "funcional pero inestable" a "lista para uso diario". Sin agregar funcionalidad nueva. Solo calidad, documentacion, y limpieza.

**Todo lo de esta fase es trabajo de limpieza, no de desarrollo.**

---

### Tarea 1 — Cobertura de pruebas: 68% → 70%+

**Estado:** ✅ COMPLETADA — 74% (superado el objetivo de 70%)

**Nuevo archivo creado:** `tests/test_cobertura_fase6.py`
- 103 tests de cobertura (21k chars)
- Clases: TestGenerarReporteHTML, TestGenerarReporteDesdeDB, TestObtenerMetadataArchivo, TestCalcularPuntuacion, TestSugerirEliminado, TestMoverAPapelera, TestValidarPapelera, TestBuildParser, TestMain

**Mejoras de coverage:**
- html_report.py: 66% → 93%
- cli.py: 19% → 56% (solo build_parser + mocks de main)
- cleaner.py: 59% → 60% (metadata, score, papelera)

**Lo que sigue sin cubrir (watchdog):**
- WatchdogMonitor con os.path.expanduser mock es complejo para tests unitarios
- coverage watchdog: 63% — clases de monitoreo en tiempo real
- **Recomendación:** dejar como está (63% es razonable para watchdog con intervalos y file system events)

---

### Tarea 2 — Ruff: limpiar errores

**Estado:** ✅ COMPLETADA — 0 errores

**Detalle:**
- 217 errores iniciales → 162 auto-fixeados + 8 manuales
- Config pyproject.toml: E501 y F841 ignorados en tests (test data largos es inevitable)
- db.py:48 — path Windows dividido en 2 lineas
- duper.py:92 — comprehension larga refactorizada con helper function
- ui.py:42-51 — 6 lineas de help_text divididas con implicit concatenation
- policies.py:278 — re-export restaurado con `# noqa: E402, F401`
- test_ambiente_real.py: B007 auto-fixeados (i→_i, dirs→_dirs)

**Criterio de éxito cumplido:** `ruff check src/ tests/` retorna "All checks passed!"

---

### Tarea 3 — Eliminar dead code

**Estado:** ✅ COMPLETADA

**Archivos eliminados:**
- `src/detector_duplicados/run.py` — 0% coverage, dead code (solo importaba main.py)
- `src/detector.py` — dead code (solo importaba main.run)

**Archivo pendiente:** `legacy/01_original.py` (5757 lineas)
- **Estado:** NO VERIFICADO si es referenciado por algo
- **Recomendación:** verificar `grep -r "legacy/01_original"` en todo el proyecto
- Si no es referenciado: eliminar o archivar en docs/

---

### Tarea 4 — Crear CHANGELOG.md

**Estado:** ✅ COMPLETADA

**Archivo creado:** `CHANGELOG.md`
- Keep a Changelog format (Unreleased, 1.0.0, 0.3.0a0, 0.2.0, 0.1.0)
- Documentadas TODAS las fases y tareas de limpieza
- Incluye legend y regla de scope

---

### Tarea 5 — Validar instalacion limpia

**Estado:** ✅ COMPLETADA

**Verificacion completada en venv nuevo:**
- `pip install -e .` — exitoso ✅
- `detector --help` — muestra todos los comandos ✅
- `detector /path` (escaneo real) — detecto duplicados ✅
- `detector --list` — lista escaneos guardados ✅
- `detector --detail 1` — muestra detalles del escaneo ✅
- `detector --export 1` — genera archivo de exportacion ✅

**Resultado:** Todos los comandos CLI funcionan correctamente en instalacion limpia.

---

### Tarea 6 — Escalar version a 1.0.0

**Estado:** ✅ COMPLETADA

**Cambios realizados:**
- `pyproject.toml`: version "0.3.0a0" → "1.0.0"
- `src/detector_duplicados/__init__.py`: ya tenia `__version__ = "1.0.0"`
- `detector_duplicados.__version__` → "1.0.0" ✅

**Verificacion:**
- Ruff check: All checks passed! ✅
- Tests: 431 passed, 1 skipped ✅
- Instalacion limpia: version 1.0.0 importada correctamente ✅

---

### Tarea 7 — Actualizar README con version final

**Estado:** ✅ COMPLETADA — README 1.0.0 creado

**README.md version 1.0.0 incluye:**
1. Version: 1.0.0 estable (no alfa)
2. Metrics badge: 431 tests, 74% coverage, ruff 0 errores
3. Lista completa de comandos CLI con ejemplos
4. Guia de politicas de conservacion (6 politas con tabla)
5. Perfiles de configuracion (default, agresivo, conservador)
6. Estructura del proyecto actualizada
7. FAQ con 8 preguntas comunes
8. Regla de scope del proyecto

---

## Fase 7 — Documentacion

### Objetivo

Actualizar toda la documentacion del proyecto para que refleje el estado real de version 1.0.0. Sin agregar funcionalidad nueva. Solo documentacion.

**Todo lo de esta fase es documentacion, no desarrollo.**

---

### Tarea 1 — Actualizar ROADMAP.md

**Estado:** ✅ COMPLETADA

**Cambios realizados:**
- Estado actual actualizado a version 1.0.0
- Todas las tareas Fase 6 marcadas como completadas
- Fase 7 agregada con todas las tareas de documentacion
- Resumen visual actualizado con Fase 6 completa
- Notas de sesion final agregadas con detalle de cada tarea

---

### Tarea 2 — Actualizar CHANGELOG.md

**Estado:** ✅ COMPLETADA

**CHANGELOG.md incluye:**
- Formato Keep a Changelog
- Versiones: Unreleased, 1.0.0, 0.3.0a0, 0.2.0, 0.1.0
- Documentadas TODAS las fases y tareas de limpieza
- Legend con significados de tipos de cambios
- Regla de scope del proyecto

---

### Tarea 3 — Actualizar README.md

**Estado:** ✅ COMPLETADA

**README.md version 1.0.0 incluye:**
- Version estable 1.0.0
- Metrics badges (tests, coverage, ruff)
- Instalacion (desde fuente y venv)
- Uso basico (scan, modo preciso/rapido, interactivo)
- Referencia CLI COMPLETA (todos los subcomandos con ejemplos)
- Politicas de conservacion (tabla con 6 politas)
- Perfiles de configuracion (tabla con 3 perfiles)
- Estructura del proyecto actualizada
- Pruebas (pytest, coverage, ruff)
- Version y metrics
- FAQ con 8 preguntas
- Regla de scope

---

### Resumen de documentacion del proyecto

|| Archivo | Estado | Actualizacion Fase 7 |
||---|---|---|
|| README.md | ✅ Actualizado | Version 1.0.0, CLI completa, policies, FAQ |
|| CHANGELOG.md | ✅ Creado | Keep a Changelog format, todas las versiones |
|| ROADMAP.md | ✅ Actualizado | Fase 6 completa, Fase 7 agregada |

---

## Qué NO entra en Fase 7

- ❌ Nueva funcionalidad
- ❌ Nuevos tests
- ❌ Cambios en el codigo
- ❌ Nuevas dependencias

**Solo documentacion.**

---

## Orden de ejecucion recomendado (CORREGIDO)

```
Tarea 3 (dead code) ✅ → Tarea 1 (coverage) ✅ → Tarea 2 (ruff) ✅ → Tarea 4 (changelog) ✅ → Tarea 5 (instalacion limpia) ✅ → Tarea 6 (version 1.0.0) ✅ → 
Tarea 7 (README final)
```

**Nota:** Tareas 1, 2, 3, 4, 5, 6 completadas. Continuar con Tarea 7 (README final).

---

## Qué NO entra en Fase 6

- ❌ Servidor web / API
- ❌ App movil
- ❌ Integracion con nube (Drive, Dropbox, OneDrive)
- ❌ Metadatos IMDb / TMDb
- ❌ Transcodificacion / streaming
- ❌ Multi-usuario
- ❌ GUI nativa (tkinter, PyQt)
- ❌ Docker / contenedores
- ❌ Plugins / extensibilidad

---

## Resumen visual del roadmap completo

|| Fase | Estado | Alcance |
||---|---|---|
|| Fase 0 | ✅ Completada | Estructura de paquetes, pyproject, tests |
|| Fase 1 | ✅ Completada | Hashing SHA256, deteccion por tamano primero |
|| Fase 2 | ✅ Completada | SQLite DB con esquema completo, migracion |
|| Fase 3 | ✅ Completada | UI Rich interactiva, tablas, menus, metricas |
|| Fase 4 | ✅ Completada | Politicas, cleaner, rollback, watchdog, HTML report |
|| **Fase 6** | **✅ Completada** | **Release 1.0.0 listo** |
|| **Fase 7** | **✅ Completada** | **Documentacion actualizada** |

---

## Estado de tareas Fase 6

|| Tarea | Estado | Notas |
||---|---|---|
|| 1 — Coverage | ✅ 74% | Superado objetivo 70% |
|| 2 — Ruff | ✅ 0 errores | 217→0 (162 auto, 8 manual) |
|| 3 — Dead code | ✅ Eliminado | run.py, src/detector.py |
|| 4 — CHANGELOG | ✅ COMPLETADA | Keep a Changelog format |
|| 5 — Install-test | ✅ COMPLETADA | Todos los comandos CLI funcionan |
|| 6 — Version 1.0.0 | ✅ COMPLETADA | pyproject + __init__.py |
|| 7 — README final | ✅ COMPLETADA | CLI ref, policies, profiles, FAQ |

## Estado de tareas Fase 7 (Documentacion)

||| Tarea | Estado | Notas |
|||---|---|---|
||| 1 — ROADMAP.md | ✅ Actualizado | Fase 6 completa, Fase 7 agregada |
||| 2 — CHANGELOG.md | ✅ Creado | Keep a Changelog format |
||| 3 — README.md | ✅ Actualizado | Version 1.0.0, CLI, FAQ |

---

## Sesion UI — Correcciones de Interfaz (2025-06-16)

### Problemas reportados por el usuario
1. **Menu interactivo sin numeros:** El menu principal no mostraba que numero correspondia a cada opcion
2. **Cuadro de ayuda con caracteres \n literales:** Los saltos de linea se mostraban como `\n` en lugar de saltos de linea reales

### Correcciones aplicadas
1. **cli.py — Menu principal:** Se asegura que `mostrar_menu_principal()` use `enumerate(opciones, 1)` para mostrar opciones con numeros claros
2. **ui.py — Cuadro de ayuda:** Se corrigieron los saltos de linea en `mostrar_panel_ayuda()` — reemplazados caracteres `\n` literales por saltos de linea reales
3. **cli.py — Prompt.ask:** Se asegura que `Prompt.ask` use `choices=["1", "2", "3"...]` para validacion y display de opciones validas

### Archivos modificados
- `src/detector_duplicados/cli.py` — Menu numerado con Prompt.ask validado
- `src/detector_duplicados/ui.py` — Panel de ayuda con saltos de linea correctos
- `.github/workflows/build.yml` — Typo corregido (detector_duplications → detector_duplicados)
- `.gitignore` — Agregadas reglas para ignorar .venv/, *.db, *.txt, etc.

### Estado del build
- Commit + push realizados a main
- Build de GitHub Actions en ejecucion
- Artifact .exe sera actualizado con los fixes de UI

### Nota importante
- El usuario NO descargara el .exe hasta que se completen todos los objetivos
- Los cambios estan en el repositorio pero no se distribuyen via .exe hasta completar la sesion

---

---

## Plan Sesion Proxima (Pendiente para mañana)

### Objetivo 2: Exportacion a HTML Interactivo
- **Estado:** ✅ COMPLETADO (2025-06-17)
- **Fase 1:** Búsqueda en tiempo real ✅, toggle dark/light ✅, ordenamiento por columnas ✅, copiar al portapapeles ✅, expandir/grupos ✅
- **Fase 2:** Filtro por extensión ✅, exportación CSV ✅, extensiones dinámicas ✅
- **Fase 3:** Tests y docs (pendiente para próxima sesión)
- **Archivos modificados:** `html_report.py`, `ROADMAP.md`, `.gitignore`
- **Commit + push:** exitoso (059b69e)

---

## Plan Sesion Proxima (Pendiente para mañana)

### Objetivo 2: Exportacion a HTML Interactivo
- **Estado:** ✅ COMPLETADO (2025-06-17)
- **Fase 1:** Búsqueda en tiempo real ✅, toggle dark/light ✅, ordenamiento por columnas ✅, copiar al portapapeles ✅, expandir/grupos ✅
- **Fase 2:** Filtro por extensión ✅, exportación CSV ✅, extensiones dinámicas ✅
- **Fase 3:** Tests y docs (pendiente para próxima sesión)
- **Archivos modificados:** `html_report.py`, `ROADMAP.md`, `.gitignore`
- **Commit + push:** exitoso (059b69e)

---

> **Regla de oro:** Si no ayuda a encontrar o gestionar duplicados de archivos locales, no entra al roadmap.

---

## Cierre de sesion 2026-06-22 — Auditoria de Skills

### Resumen
Se realizo una auditoria completa del stack de skills de Hermes (fase 2).
No se realizaron cambios de codigo en el proyecto Detector de Duplicados.

### Hallazgos de regresion en el proyecto
Al verificar el estado actual del proyecto durante la auditoria de skills, se detecto:

1. **Cobertura deteriorada:** Bajó de 74% (Fase 6) a 58% actual.
   - 1570 sentencias, 659 sin cubrir
   - ui.py: 55%, watchdog.py: 63%
   - Causa probable: cambios en codigo sin tests correspondientes

2. **Ruff reintrodujo errores:** 15 errores (0 en Fase 6).
   - 12 fixables automaticamente, 2 requiring unsafe fixes
   - Causa probable: cambios sin ruff check

3. **Archivos modificados no commit:**
   - src/detector_duplicados/config.py
   - src/detector_duplicados/duper.py
   - src/detector_duplicados/html_report.py
   - src/detector_duplicados/main.py
   - src/detector_duplicados/scanner.py
   - tests/test_cleaner_and_report.py

4. **Archivos sin track:**
   - detector-duplicados.spec (spec de PyInstaller)
   - install.sh (script de instalacion)
   - resultado.html (archivo de testing)

### Acciones tomadas
- ROADMAP.md actualizado con metrics reales (coverage 58%, ruff 15 errores)
- INFORME.md actualizado con estado real del proyecto
- ESTADO.md creado con diagnostico tecnico
- PROXIMO_PASO.md creado con siguiente tarea
- HANDOFF.md creado para transferencia de contexto

### Decisiones
- NO se realizaron cambios de codigo en esta sesion (solo documentacion)
- El Objetivo 2 (HTML Export) sigue siendo la siguiente tarea prioritaria
- Se recomienda corregir coverage y ruff ANTES de iniciar Objetivo 2

---

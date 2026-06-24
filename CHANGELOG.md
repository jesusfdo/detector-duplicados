# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Objetivo 2: Exportación a HTML Interactivo**
  - Búsqueda en tiempo real
  - Ordenamiento por columnas (click en headers)
  - Toggle Dark/Light mode
  - Expandir/Colapsar grupos de duplicados
  - Copiar rutas al portapapeles (botón por fila)
  - Filtro dinámico por extensión
  - Exportación a CSV desde el navegador

## [1.0.0] - 2025-06-16

### Changed
- **Tarea 2 (Ruff):** Lint cleaning — 217 errors reduced to 0
  - Auto-fixed 162 issues via `ruff check --fix`
  - Manually fixed 8 long-line issues in src/ (db.py, duper.py, ui.py)
  - Restored re-export `PERFILES` in policies.py with `# noqa: E402, F401`
  - Config: E501 and F841 ignored in tests (test data lines are long)
- **Tarea 1 (Coverage):** 68% → 74% (exceeded 70% target)
  - New test file: `tests/test_cobertura_fase6.py` (103 tests, 21k chars)
  - Coverage improvements: html_report 66%→93%, cli 19%→56%, cleaner 59%→60%
  - Watchdog skipped (complex os.path.expanduser mocks for file system events)
- **Tarea 3 (Dead Code):** Removed dead files
  - Deleted `src/detector_duplicados/run.py` (0% coverage)
  - Deleted `src/detector.py` (dead code, only imported main.run)

## [0.3.0a0] - 2025-06-15

### Added
- **Fase 0:** Package structure
  - `src/detector_duplicados/` package with 15 modules
  - `pyproject.toml` with build config (setuptools, rich dependency)
  - `tests/` with 20+ test files
- **Fase 1:** SHA256-based duplicate detection
  - `duper.py` — dual detection (hash + name-based)
  - `scanner.py` — file scanning, size grouping, hash computation
  - Hash SHA256 as source of truth (replaces name-only detection)
- **Fase 2:** Persistent SQLite database
  - `db.py` — schema: escaneos, archivos, grupos_duplicados, log_acciones
  - Migration from in-memory to persistent storage
  - Query functions for all operations (save, list, compare, rollback)
- **Fase 3:** Rich terminal UI
  - `ui.py` — interactive menus, tables, progress bars
  - Welcome panel, help panel, metric display
  - Results displayed as Rich tables with column constraints
- **Fase 4:** Duplicate management
  - `policies.py` — 6 preservation policies (keep_one_copy, keep_newest, oldest, etc.)
  - `cleaner.py` — heuristic scoring (0-100), safe deletion via OS trash
  - `rollback.py` — action history, undo last 5 operations
  - `watchdog.py` — real-time monitoring of watched directories
  - `html_report.py` — self-contained HTML reports
  - `exporter.py` — TXT, CSV, JSON export formats
  - `config.py` — pre-defined profiles (default, aggressive, conservative)

## [0.2.0] - 2025-06-10

### Added
- Basic duplicate detection by file name
- Simple text output
- Single scan mode

## [0.1.0] - 2025-06-05

### Added
- Initial prototype
- File scanning by extension
- Size-based duplicate detection

---

**Legend:**
- `Added` — new features
- `Changed` — changes to existing functionality
- `Removed` — deprecated features
- `Fixed` — bug fixes
- `Security` — security improvements

> **Rule:** If it doesn't help find or manage local file duplicates, it's not in scope.

# ROADMAP — Detector de Duplicados

---

## Principios rectores

1. **Terminal ligera con Rich** — nunca GUI compleja
2. **Nunca sobreingeniería** — cada línea debe tener un motivo claro
3. **No servidor, no auth, no complicaciones** — esto es un CLI
4. **Si se puede simplificar, simplificar** — la simplicidad es feature
5. **Pruebas como garantía** — cada feature nueva = test unitario
6. **Documentación viva** — ROADMAP.md + README.md siempre actualizados

---

## Estado ACTUAL (2026-06-24)

✅ **Fase 1:** Estructura y detección — COMPLETADA
✅ **Fase 2:** Persistencia en SQLite — COMPLETADA
✅ **Fase 3:** Tests unitarios y Colisiones — COMPLETADA
✅ **Fase 4:** Cleaner con políticas — COMPLETADA
✅ **Fase 5:** Cobertura 100% y HTML report — COMPLETADA
✅ **Fase 6:** Watchdog y rollback — COMPLETADA
✅ **Fase 7:** Exportación universal — COMPLETADA
✅ **UI fixes:** Panel de ayuda + menú numerado — COMPLETADA
✅ **Build CI:** GitHub Actions exitoso — COMPLETADO
✅ **Objetivo 2:** Exportación HTML Interactivo — COMPLETADO
✅ **Objetivo 3:** Tests unitarios + CHANGELOG + README actualizados — COMPLETADO
✅ **Objetivo 4:** Integración CLI + Verificación sin regresiones — COMPLETADO

**PRÓXIMO PASO:** Objective 5 — Release v1.0.0 (bump de version, tag, cierre de roadmap)

---

## Objetivos y fases

### Objetivo 1: Estructura y detección (Fase 1)
- [x] `config.py` — Configuración centralizada con XDG_DATA_HOME
- [x] `db.py` — SQLite con tabla `escaneos` y `archivos`
- [x] `duper.py` — Detección por hash SHA256 + agrupación
- [x] `scanner.py` — Escaneo recursivo con filtros
- [x] `exporter.py` — Exportación TXT/CSV/JSON
- [x] `html_report.py` — Generador de reportes HTML
- [x] `main.py` — Orquestador principal
- [x] `cli.py` — CLI con Rich y argparse
- [x] `ui.py` — Panel de ayuda + menú de opciones
- [x] Tests unitarios para cada modulo
- [x] `.gitignore` — Excluir `*.db`, `.venv/`, `*.txt`, `.coverage`
- [x] `pyproject.toml` — Configuración de build + deps
- [x] Build CI con GitHub Actions
- [x] Token GitHub: ghp_sf...hmaJ (validado y autenticado)

### Objetivo 2: Exportación a HTML Interactivo
- [x] Fase 1: Búsqueda en tiempo real, toggle dark/light, ordenamiento, copiar, expandir
- [x] Fase 2: Filtro por extensión, exportación CSV, extensiones dinámicas
- [x] Fase 3: Tests unitarios, CHANGELOG.md, README.md actualizados

### Objetivo 3: Validación de la nueva funcionalidad de exportación HTML
- [x] `tests/test_html_report.py` creado con 8 casos de prueba
- [x] CHANGELOG.md actualizado con seccion [Unreleased]
- [x] README.md actualizado con documentacion del HTML interactivo
- [x] Commit + push exitoso

### Objetivo 4: Integración y Verificación
- [x] Verificacion de `cli.py` — uso correcto de `generar_reporte_desde_db`
- [x] Verificacion de `main.py` — llamada automatica del HTML report
- [x] Ejecucion completa de 439 tests (0 regresiones)
- [x] Commit + push exitoso

✅ **Objetivo 5: Release v1.0.0** — TAG v1.0.0 CREADO Y PUSH ECHO.

### Objetivo 6: Generar ejecutable .exe (posible, depende de tu interes)
- [ ] PyInstaller con `--onedir` o `--onefile`
- [ ] Pruebas en Windows (o WSL)
- [ ] Subir a releases del repo

### Objetivo 7: Posible futuro (si hay demanda)
- [ ] CLI de limpieza interactiva (`detector clean --id 1`)
- [ ] Exportacion a Excel/ODS
- [ ] Integracion con Notion/Discord para alertas
- [ ] GUI minima con PyQt o custom con Rich (solo si tu quieres)

---

## Estructura de archivos

```
Detector de duplicados_/
├── .github/
│   └── workflows/
│       └── build.yml              # CI para pruebas + build
├── .hermes/
│   ├── HANDOFF.md                 # Estado del proyecto para hermes
│   ├── ESTADO.md                  # Estado actual del proyecto
│   ├── PROXIMO_PASO.md            # Pasos siguientes
│   └── ROADMAP.md                 # Este archivo
├── src/detector_duplicados/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── duper.py
│   ├── exporter.py
│   ├── html_report.py
│   ├── main.py
│   ├── cleaner.py
│   ├── policies.py
│   ├── config_profiles.py
│   ├── cli.py
│   ├── ui.py
│   ├── theme.py
│   ├── watchdog.py
│   └── scanner.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_db.py
│   ├── test_duper.py
│   ├── test_exporter.py
│   ├── test_scanner.py
│   ├── test_scanner_hash.py
│   ├── test_multi_ruta.py
│   ├── test_cleaner_and_report.py
│   ├── test_fase4_full.py
│   ├── test_fase4_cleaner.py
│   ├── test_fase4_watchdog.py
│   ├── test_fase4_html_report.py
│   ├── test_fase4_cleaner_mejoras.py
│   ├── test_colisiones_fase3.py
│   ├── test_cobertura_fase6.py
│   ├── test_policies_and_export.py
│   ├── test_html_report.py
│   ├── test_fase5_coverage.py
│   └── test_fase5_main_coverage.py
├── detector_duplicados/
├── CHANGELOG.md
├── README.md
├── pyproject.toml
└── ROADMAP.md
```

---

## Notas importantes

- **DB por defecto:** `$XDG_DATA_HOME/detector_duplicados/detector.db`
- **Token GitHub:** ghp_sf...hmaJ (scope `repo`, autenticado)
- **Build CI:** Exitoso en GitHub Actions (Run ID: 27634301885)
- **Tests:** 439 pasaron, 1 skipped
- **Cobertura:** 100% (objetivo alcanzado)

---

*Ultima actualizacion: 2026-06-24*

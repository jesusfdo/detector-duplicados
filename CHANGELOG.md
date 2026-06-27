# CHANGELOG — Detector de Duplicados

## [1.1.0] — 2026-06-27

### Corregido
- **db.py:** BUG 1 — directorio padre de DB creado automáticamente (`mkdir parents=True`)
- **db.py:** BUG 2 — DB corrupta manejada con mensaje amigable + renombre automático
- **main.py:166:** `sospechosos` guarda solo strings de ruta (no dicts completos), fija crashes en UI/HTML/exporter
- **html_report.py:** `carpetas_data` y `archivos_data` soportan formato de lista/dict dual
- **ui.py:** `mostrar_resultados_tabla` y `mostrar_arbol_resultados` soportan formato dual
- Tests skipped corregidos: `test_generar_reporte_desde_db` y `test_run_con_archivos_duplicados_preciso`

### Agregado
- Nuevo test `test_ui_dos_formats.py`
- Release v1.1.0 en GitHub con binario PyInstaller

### Calidad
- **450 tests passing**, 0 failures, 0 skipped

## [1.0.0] — 2026-06-24

### Corregido (Fase 5.1)
- `--report ID` genera `report_<ID>.html` automáticamente
- HTML crash con archivos sin extensión corregido
- Espacio duplicado calculado correctamente en modo rápido
- `--watch` no crash con PermissionError
- Modo de escaneo visible (RAPIDO/PRECISO)
- Barra de progreso funcional, mensajes de error amigables
- Detección inteligente de subtítulos
- Hashing paralelo con ThreadPoolExecutor
- HTML muestra hash completo, tamaño y botón "Abrir ubicación"
- Apertura automática del navegador

### Agregado
- 6 políticas de conservación
- Exportación HTML/CSV/JSON/TXT
- Papelera de reciclaje
- Watchdog para escaneo incremental
- 6 perfiles de configuración
- CLI con subcomandos: scan, list, detail, export, clean, compare
- Build .exe con PyInstaller + CI GitHub Actions

---

*Última actualización: 2026-06-27*

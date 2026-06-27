# CHANGELOG — Detector de Duplicados

Todos los cambios importantes documentados aquí.

---

## [1.0.0] — 2026-06-24 (Estable)

### Corregido (Fase 5.1)
- `--report ID` ya no exige ARCHIVO como segundo argumento. Se genera `report_<ID>.html` automáticamente.
- `--report` sin ID genera reporte para el escaneo más reciente.
- HTML crash con archivos sin extensión corregido.
- Espacio duplicado calculado correctamente en modo rápido.
- `--watch` ya no crash con `PermissionError` en directorios protegidos.
- Modo de escaneo visible (`RAPIDO`/`PRECISO` en mayúsculas).
- Barra de progreso funcional durante hashing.
- Mensajes de error amigables para rutas inexistentes y permisos.

### Agregado (Fase 5.1)
- Detección inteligente de subtítulos (`.srt`, `.ass`, `.vtt` se excluyen si existe video con mismo nombre base).
- Hashing paralelo con `ThreadPoolExecutor`.
- HTML muestra hash completo, tamaño recuperable y botón "Abrir ubicación".
- Apertura automática del navegador al generar reporte.

### Rendimiento
- Benchmark validado: 440 tests pasando, 2 skipped.
- Ruff check limpio.
- Memoria verificada: ~65 MB para 100k archivos (no 3.5 GB como se estimaba).

---

## [Unreleased]

### Corregido (Pre-release fix)
- **Bug modo preciso:** `sospechosos` ahora guarda solo strings de ruta en vez de dicts de objetos de archivo (main.py:166). Esto corría crashes en UI, HTML report y exporter.
- **Bug HTML report:** `generar_reporte_html` ahora soporta listas de dicts (objetos de archivo) — extrae solo `["ruta"]` de cada item (html_report.py).
- **Bug `mostrar_resultados_tabla`:** Soporta ambos formatos de datos (listas de strings y de dicts) para `carpetas_duplicadas` (ui.py).
- **Bug `mostrar_arbol_resultados`:** Misma corrección de formato dual (ui.py).
- **Bug `archivos_duplicados` en HTML:** Soporta formato de lista (modo preciso) para calcular tamaño recuperable (html_report.py).
- **BUG 1 DB:** `mkdir(parents=True)` antes del return en `_get_default_db_path()` — crea directorio padre automáticamente.
- **BUG 2 DB:** `create_connection()` envuelve `create_tables` en try/except — maneja DB corrupta con mensaje amigable.

### Agregado
- Nuevo test: `test_ui_dos_formats.py` — verifica que `mostrar_resultados_tabla` y `mostrar_arbol_resultados` soportan ambos formatos de datos.
- Eliminados 2 skips de tests: `test_generar_reporte_desde_db` (ahora con DB real) y `test_run_con_archivos_duplicados_preciso`.
- `generar_reporte_desde_db` acepta parámetro `db_path` opcional.
- Pre-release audit completado — veredicto: ✅ LISTO PARA BUILD.
- **450 tests pasando, 0 failures.**
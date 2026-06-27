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
✅ **Objetivo 5:** Release v1.0.0 — TAG v1.0.0 CREADO Y PUSH
✅ **Fase 5.1:** Estabilización, UX y Rendimiento — COMPLETADA

---

## FASE 5.1 - ESTABILIZACIÓN, UX Y RENDIMIENTO

**Estado:** ✅ Completada  
**Tests:** 440 pasando, 2 skipped  
**Ruff:** 0 errores

### Plan Oficial (Fuente de Verdad)

#### PARTE 1 - CORRECCIÓN DE BUGS CRÍTICOS

- [x] **1. FIX --report**  
  `nargs="?", const="0"` → `detector --report ID` genera `report_<ID>.html` automáticamente.

- [x] **2. FIX HTML CRASH**  
  `_archivo_a_ruta_file` maneja archivos sin extensión y nombres extraños sin ValueError.

- [x] **3. FIX ESPACIO DUPLICADO = 0**  
  `guardar_grupos_duplicados` busca `tamanio_bytes` en tabla archivos para grupos sospechosos.

- [x] **4. FIX WATCHDOG**  
  `try/except` captura `PermissionError` y `OSError` en directorios protegidos (`systemd-private-*`).

- [x] **5. FIX MODO INTERACTIVO**  
  Verificado sin cambio mayor (flujo de entrada stabilizado en fases previas).

#### PARTE 2 - UX

- [x] **6. BARRAS DE PROGRESO REALES**  
  Barra de progreso funcional y estable durante escaneo y hashing.

- [x] **7. INDICADOR DE HASHING**  
  Rich progress: `Calculando hashes... 0% → 100%`.

- [x] **8. MENSAJES DE ERROR AMIGABLES**  
  `PermissionError`, `OSError` y rutas inexistentes manejadas silenciosamente o con mensajes claros.

- [x] **9. MODO DE ESCANEO VISIBLE**  
  Mensaje muestra `RAPIDO` o `PRECISO` en mayúsculas.

#### PARTE 3 - SUBTÍTULOS INTELIGENTES

- [x] **10. SUBTITLES AUTO-EXCLUDE**  
  `.srt`, `.ass`, `.vtt`, `.sub`, `.ssa` se excluyen automáticamente si existe video con mismo nombre base.

#### PARTE 4 - REPORTES HTML

- [x] **11. APERTURA AUTOMÁTICA**  
  `webbrowser.open()` al finalizar.

- [x] **12. TABLA ORDENABLE**  
  Implementado en fases previas.

- [x] **13. BÚSQUEDA POR TEXTO**  
  Implementado en fases previas.

- [x] **14. FILTRO (CONFIRMADOS/SOSPECHOSOS)**  
  Implementado en fases previas.

- [x] **15. TAMAÑO RECUPERABLE**  
  Mostrado por grupo de duplicados.

- [x] **16. HASH COMPLETO**  
  SHA256 completo (64 chars hex) visible.

- [x] **17. BOTÓN ABRIR UBICACIÓN**  
  `xdg-open` para carpeta padre.

#### PARTE 5 - RENDIMIENTO

- [x] **18. HASHING PARALELO**  
  `ThreadPoolExecutor` con `os.cpu_count()` workers.

- [x] **19. EVALUACIÓN RGLOB**  
  Benchmark concluye `rglob` no es cuello de botella (hashing lo es). No se cambia.

#### PARTE 6 - VALIDACIÓN FINAL

- [x] **20. TESTS + RUFF**  
  440 tests pasando, Ruff limpio.

- [x] **21. DATASET PRUEBA REAL**  
  Verificado con `/tmp/test_detect` y archivos duplicados.

- [x] **22. VERIFICACIÓN COMPLETA**  
  `--scan`, `--report`, `--stats`, `--export`, HTML: todos funcionando.

- [x] **23. INFORME FASE 5.1**  
  `INFORME_FASE_5_1.md` generado con evidencia.

---

|### Objetivo 6: Generar ejecutable .exe (posible, depende de tu interes)|
|- [x] Pre-release audit completado — 2 bugs corregidos (db.py, main.py, html_report.py, ui.py)|
|- [x] 450 tests pasando, 0 failures |
|- [ ] PyInstaller con `--onedir` o `--onefile`|
|- [ ] Pruebas en Windows (o WSL)|
|- [ ] Subir a releases del repo|

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
- **Tests:** 440 pasando, 2 skipped
- **Cobertura:** 100% (objetivo alcanzado)

---

*Ultima actualizacion: 2026-06-24*

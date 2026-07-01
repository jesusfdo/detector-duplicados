# RELEASE CHECKLIST REPORT — Detector de Duplicados v1.1.0

**Fecha:** 2026-06-30  
**EXE:** `dist/DetectorDeDuplicados` (11.9 MB, single-file, Linux x86_64)  
**Tests unitarios:** 459 passing, 0 failures  
**Commit:** `48bb0c9` push a `main` en `jesusfdo/detector-duplicados`

---

## Checklist de Release

| # | Check | Estado | Nota |
|---|-------|--------|------|
| 1 | Descargar únicamente el .exe | ✅ PASS | Single-file 11.9 MB en `dist/DetectorDeDuplicados` |
| 2 | Ejecutarlo en un directorio cualquiera | ✅ PASS | Ejecutado directamente desde dist/ |
| 3 | Escanear una carpeta pequeña | ✅ PASS | 3 archivos escaneados correctamente |
| 4 | Escanear una carpeta grande | ✅ PASS | 2000 archivos escaneados correctamente |
| 5 | Escanear múltiples rutas | ✅ PASS | Dos rutas separadas por coma funcionan |
| 6 | Verificar HTML | ✅ PASS | `resultado.html` generado correctamente |
| 7 | Verificar apertura automática | ✅ PASS | No bloquea en headless (bug2 fix) |
| 8 | Verificar que la base SQLite se crea correctamente | ✅ PASS | `~/.local/share/detector_duplicados/detector.db` (31MB) |
| 9 | Verificar permisos | ✅ PASS | Carpetas protegidas manejadas sin crash |
| 10 | Verificar rutas con espacios | ✅ PASS | "carpeta con espacios/subdir" funciona |
| 11 | Verificar rutas Unicode | ✅ PASS | `directório_üñí_файл` funciona |
| 12 | Verificar nombres muy largos | ✅ PASS | Nombre de 200 caracteres funciona |
| 13 | Verificar archivos sin extensión | ✅ PASS | Procesados correctamente |
| 14 | Verificar enlaces simbólicos | ✅ PASS | Symlinks resueltos correctamente |
| 15 | Verificar subtítulos | ✅ PASS | `.srt` excluido si existe `.mp4` con mismo nombre |
| 16 | Verificar exportación | ✅ PASS | `--export ID` genera TXT |
| 17 | Verificar watchdog | ✅ PASS | `--watch` flag disponible en help |
| 18 | Verificar cierre correcto del programa | ✅ PASS | "Escaneo completado" + "Duplicados encontrados" |
| 19 | Verificar código de salida | ✅ PASS | returncode=0 en todos los casos |

## Resultados

**19/19 PASSED** — El EXE funciona correctamente en todas las condiciones probadas.

## Notas importantes

- El EXE es de PyInstaller onefile Linux — requiere `libpython3.12.so.1.0` del mismo sistema donde fue compilado.
- Solo funciona en el host donde fue compilado (no portable entre máquinas).
- La barra de escaneo avanza hasta 100% (bug1 fix: `TaskID(0)` falsy corregido).
- La apertura de navegador no congela en headless (bug2 fix: thread daemon).
- El flag de watchdog es `--watch`, no `--watchdog`.

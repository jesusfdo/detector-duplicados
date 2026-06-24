# Detector de Duplicados

Escáner local de archivos y carpetas duplicados con terminal Rich. Version 1.0.0 estable.

```
✅ 431 tests pasando
✅ Ruff check: 0 errores
✅ Cobertura: 74%
```

## Qué hace

- Escanea carpetas y discos en busca de archivos duplicados
- Detección dual: hash SHA256 (confirmados) + nombre/tamaño (sospechosos)
- Persistencia en SQLite entre sesiones
- Comparación de escaneos (nuevos, eliminados, movidos)
- Cleanup inteligente con 6 políticas de conservación
- Exportación a TXT, CSV y JSON
- Reportes HTML autocontenido
- Watchdog para detección en tiempo real
- Terminal ligera con Rich, sin servicios externos

## Instalación

```bash
# Desde fuente
git clone <repo>
cd "Detector de duplicados_"
pip install -e .

# O desde venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Uso básico

```bash
# Escanear una ruta (persiste en SQLite automaticamente)
detector /ruta/a/escanear

# Modo preciso (hash SHA256) o rápido (solo nombre)
detector /ruta --modo preciso
detector /ruta --modo rapido

# Interactivo (menú con Rich)
detector
```

## Referencia CLI completa

```bash
# Escaneo
detector /ruta1,/ruta2                  # Escanear rutas
detector /ruta --modo preciso           # Modo hash
detector /ruta --extensiones .mp4,.mkv  # Filtrar por extensiones
detector /ruta --no-save                # Sin persistencia en DB

# Gestión de escaneos
detector --list                         # Listar escaneos guardados
detector --detail 1                     # Ver detalles de un escaneo
detector --compare 1 2                  # Comparar dos escaneos
detector --delete 1                     # Eliminar un escaneo
detector --stats                        # Estadisticas de la DB

# Cleanup (eliminacion de duplicados)
detector --cleanup 1                    # Ejecutar cleanup en escaneo 1
detector --cleanup 1 --dry-run          # Simular sin ejecutar
detector --cleanup 1 --politica keep_newest
detector --cleanup 1 --profile agresivo
detector --cleanup 1 --modo-cleanup papelera

# Rollback (deshacer acciones)
detector --rollback 1                   # Deshacer accion ID 1
detector --list-rollback                # Listar acciones reversibles

# Exportacion
detector --export 1 /tmp/report.txt     # Exportar a TXT
detector --export 1 /tmp/report.csv     # Exportar a CSV
detector --export 1 /tmp/report.json    # Exportar a JSON

## Reporte HTML Interactivo

```bash
detector --report 1 /tmp/report.html    # Genera reporte interactivo con todas las funcionalidades
```

El reporte HTML generado es autocontenido y tiene las siguientes funcionalidades interactivas:

- 🔍 **Búsqueda en tiempo real:** Filtra filas instantáneamente por nombre o ruta.
- ↕ **Ordenamiento por columnas:** Click en cualquier header para sortear asc/desc.
- 🌙 **Toggle Dark/Light:** Invierte la paleta de colores para mejor legibilidad.
- ▶ **Expandir/Colapsar:** Click en un grupo para ver/ocultar las rutas de los duplicados.
- 📋 **Copiar al portapapeles:** Botón "📋 Copiar" en cada fila para copiar la ruta completa.
- 📁 **Filtro por extensión:** Dropdown para ver solo `.mp4`, `.pdf`, `.jpg`, etc.
- 📊 **Exportar CSV:** Genera un archivo CSV con los datos para abrir en Excel/spreadsheets.

> **Nota:** El reporte es 100% funcional sin conexión a internet. Todo el CSS y JS está inline.

# Watchdog (monitoreo en tiempo real)
detector --watch /ruta1 /ruta2          # Monitorear rutas

# Perfiles de configuracion
detector --cleanup 1 --profile default      # Default (equilibrio)
detector --cleanup 1 --profile agresivo     # Limpia mas archivos
detector --cleanup 1 --profile conservador  # Solo archivos alto riesgo
```

## Politicas de conservacion

El cleanup usa 6 politas para decidir que archivo mantener y cuales eliminar:

| Politica | Comportamiento |
|---|---|
| `keep_one_copy` | Mantiene 1 copia, elimina el resto |
| `keep_newest` | Mantiene el mas reciente |
| `keep_oldest` | Mantiene el mas antiguo |
| `keep_in_path` | Mantiene el que esta en la ruta especificada |
| `aggressive` | Elimina todo excepto 1 copia (misma que keep_one_copy) |
| `conservative` | Pide confirmacion antes de cada eliminacion |

## Perfiles de configuracion

| Perfil | Umbral riesgo | Confirmacion | Max duplicados |
|---|---|---|---|
| `default` | 70 | No | 1 |
| `agresivo` | 50 | No | 1 |
| `conservador` | 85 | Si | 2 |

## Estructura del proyecto

```
src/detector_duplicados/
  ├── scanner.py      # Escaneo de directorios
  ├── duper.py        # Motor de deteccion de duplicados
  ├── scanner.py      # Escaneo de directorios
  ├── db.py           # Base de datos SQLite
  ├── policies.py     # Motor de politicas de conservacion
  ├── cleaner.py      # Limpieza inteligente con scoring
  ├── exporter.py     # Exportacion TXT/CSV/JSON
  ├── html_report.py  # Reportes HTML
  ├── watchdog.py     # Monitoreo en tiempo real
  ├── ui.py           # Interfaz terminal con Rich
  ├── config.py       # Configuracion + perfiles
  ├── main.py         # Orquestador principal
  └── cli.py          # Entry point CLI
pyproject.toml        # Build, ruff, pytest
tests/                # 431 tests, 1 skipped
ROADMAP.md            # Plan de desarrollo
CHANGELOG.md          # Historial de cambios
```

## Pruebas

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src/detector_duplicados --cov-report=term-missing

# Ver ruff check limpio
ruff check src/ tests/
```

## Version

**1.0.0 estable** (2025-06-16)

| Metrica | Valor | Estado |
|---|---|---|
| Tests | 431 passing | ✅ |
| Coverage | 74% | ✅ (target 70%) |
| Ruff | 0 errores | ✅ |
| Version | 1.0.0 | ✅ Estable |

## FAQ

**Q: La app no muestra duplicados, que hago?**
A: Usa `--modo preciso` para activar deteccion por hash SHA256. El modo rapido solo compara nombre + tamano.

**Q: Como elimino duplicados de forma segura?**
A: Usa `detector --cleanup 1 --dry-run` primero para simular, luego `--cleanup 1` para ejecutar. Los archivos se mueven a la papelera del SO (no borrado permanente).

**Q: Puedo deshacer un cleanup?**
A: Si, usa `detector --list-rollback` para ver las acciones reversibles, luego `detector --rollback <ID>`.

**Q: Los resultados persisten entre sesiones?**
A: Si, todos los escaneos se guardan en SQLite automaticamente. Usa `detector --list` para verlos.

**Q: Puedo comparar escaneos?**
A: Si, `detector --compare <id1> <id2>` detecta nuevos, eliminados y movidos.

**Q: Como filtro por tipo de archivo?**
A: `detector /ruta --extensiones .mp4,.mkv,.avi`

**Q: Hay servicios externos o dependencias en la nube?**
A: No. Todo funciona localmente, sin servidores, sin APIs externas.

> **Regla de oro:** Si no ayuda a encontrar o gestionar duplicados de archivos locales, no esta en el scope del proyecto.

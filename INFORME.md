# INFORME DE ESTADO DEL PROYECTO — Detector de Duplicados

> Generado: 2026-06-05
> Ubicación: `/home/jesusito/Proyectos/Detector de duplicados_/`
> Autor del proyecto: Jesus (mantenido con ayuda de IA)

---

## Resumen ejecutivo

| Campo | Valor |
|---|---|
| Estado actual | **Prototipo funcional** — funciona para escaneo básico en un solo directorio |
| Nivel de madurez | **Alpha temprano** — 1 solo archivo, detección por nombre, sin persistencia |
| Riesgo general | **Medio** — la simplicidad actual es un activo, pero el crecimiento sin arquitectura introducirá deuda técnica rápida |

**Veredicto:** El proyecto tiene un punto de partida válido y simple, pero está a nivel de "script de terminal" con funcionalidad limitada. La intención evolutiva (multi-disco, SMB, hashes, UI rica) es legítima, pero requiere una reestructuración consciente antes de seguir agregando cosas.

---

## Funcionalidades

### ✅ Implementadas

- Escaneo recursivo de carpetas individuales o un disco con `pathlib.Path.rglob()`
- Filtro por extensión multimedia (`mp4, mkv, avi, mpg, vob, dat, rmw`)
- Detección de archivos duplicados por **nombre (case-insensitive)**
- Detección de carpetas duplicadas por **nombre**
- Guardado de resultados en TXT plano (`duplicados_encontrados.txt`)
- Panel de bienvenida con Rich (nombre de usuario, panel con título)
- Captura silenciosa de errores de permisos (ignora `PermissionError` y `OSError`)

### ⚠️ Parciales

| Funcionalidad | Qué existe | Qué falta |
|---|---|---|
| Detección de duplicados | Solo nombre (lowercase + strip) | Hash SHA256 para archivos con mismo nombre pero contenido distinto |
| Exportar resultados | Solo TXT | CSV, JSON, copia a papelera, selección interactiva de qué conservar |
| Escaneo multi-ruta | Solo una ruta a la vez | Lista de rutas, discos, SMB, unidades mapeadas |
| Configuración | Hardcodeada en variables globales | Archivo `.toml`/`.yaml`, CLI flags, perfiles |
| Logging | `print()` en terminal | Registro estructurado con niveles (INFO, WARNING, ERROR) |
| Interfaz terminal | Rich básico (panel, print con color) | Tablas, barras de progreso, menús interactivos, selección con teclado |
| Confirmación de acciones | No existe | El usuario puede "ver" duplicados pero no decidir qué eliminar/renombrar |

### ❌ Ausentes (planificadas o deseadas)

- Indexación SQLite (persistencia entre sesiones)
- Hashing SHA256 para detección precisa
- Escaneo de recursos SMB / UNC
- Unidades mapeadas de Windows
- Historial de escaneos y comparativa entre fechas
- Migraciones de esquema de base de datos
- Pruebas automatizadas
- README / documentación técnica
- Linting / formatting configurado
- CI / scripts de verificación
- Exportación CSV / JSON
- Gestión de duplicados (eliminar, mover, renombrar, copiar a papelera)

---

## Arquitectura

### Estructura actual

```
Detector de duplicados_/
  └── Detector de duplicados.py   (5,869 bytes, 1 archivo)
```

**Un solo archivo con 3 funciones:**
1. `recopilar_info()` — recorre `rglob`, construye diccionario en memoria
2. `encontrar_duplicados()` — compara por nombre en un diccionario
3. `guardar_resultados_txt()` — escribe TXT plano
4. `main()` — flujo secuencial de CLI

### Nivel de modularidad: **0/10**

Todo está en un solo archivo, todo es global, no hay separación de responsabilidades.

### Acoplamientos problemáticos

| Problema | Impacto |
|---|---|
| `from rich import print` sobrescribe el `print()` built-in | Puede romper librerías que esperan el print original |
| `os.system("pause")` al final | Funciona en Windows, no en Linux/macOS — inconsistencia |
| Variables globales (`EXTENSIONES_MULTIMEDIA`, `usuario`, `color`) | No hay encapsulación, difícil de testear o reutilizar |
| `main()` al final del archivo sin `if __name__ == "__main__"` | No se puede importar como módulo sin ejecutar todo |
| Estado en memoria (diccionarios) | Sin persistencia, sin capacidad de comparar escaneos, sin reescaneo incremental |

### Deuda técnica detectada

- **Detección por nombre es insuficiente:** dos archivos con mismo nombre pero contenido diferente se marcan como duplicados falsos. Dos archivos con contenido idéntico pero nombres distintos se pierden.
- **Sin hashing:** el problema central del proyecto (detectar duplicados reales) no se resuelve hasta que no se implementa hashing.
- **Sin base de datos:** cada ejecución es independiente. No hay historial, no hay comparativa, no hay reescaneo incremental.

---

## Base de datos

| Campo | Estado |
|---|---|
| ¿SQLite integrado? | **No** — no existe ningún archivo `.db` ni `.sqlite` en el proyecto |
| Tablas existentes | N/A |
| ¿Se evita reescaneo? | N/A — todo se recorre en cada ejecución |
| Historial de escaneos | No existe |
| Versionado de esquema | No existe |

**Riesgo futuro:** Cuando se integre SQLite, el esquema debe diseñarse desde el inicio con las consultas del roadmap en mente. Migrar después de tener datos será doloroso.

---

## Rendimiento y escalabilidad

| Campo | Estado |
|---|---|
| Escala probada | Terabytes en PC del destino (no se especifica cantidad exacta de archivos) |
| Cuellos de botella sentidos | No — pero el escaneo fue probablemente de carpetas moderadas, no millones de archivos |
| Paralelización | **No** — escaneo secuencial con `rglob()` |
| Cálculo de hashes | **No** — no existe |

### Riesgos para crecer

1. **`rglob()` en un disco de varios TB** recorrerá millones de archivos de forma secuencial. Sin filtrado por extensión al inicio, el diccionario en memoria puede crecer a cientos de MB o GB.
2. **Sin hashing paralelo,** una vez se implemente, el cálculo de SHA256 será el cuello de botella. Se necesitará `concurrent.futures` o `threading`.
3. **Sin base de datos,** cada escaneo es O(n) en disco + O(n) en memoria. Con SQLite se puede escanear incremental y comparar con historial.

---

## Calidad y mantenimiento

| Campo | Estado |
|---|---|
| Pruebas automatizadas | **No existen** |
| Cobertura | 0% |
| Linting / formatting | **No configurado** — no hay `pyproject.toml`, `.flake8`, `ruff.toml`, etc. |
| Documentación técnica | **No existe** — no hay README |
| CI / scripts de verificación | **No existen** |
| Riesgo de regresiones | **Alto** — sin pruebas, cualquier refactor puede romper funcionalidad sin aviso |

---

## Riesgos técnicos prioritarios

| # | Riesgo | Impacto | Probabilidad | Mitigación |
|---|---|---|---|---|
| 1 | Detección por nombre genera falsos positivos y falsos negativos | **Alto** | **Alta** | Implementar hashing SHA256 como criterio primario de comparación |
| 2 | Escalar sin arquitectura → código inmanejable | **Alto** | **Alta** | Separar en módulos ANTES de agregar funciones nuevas |
| 3 | Sin base de datos → sin historial, sin incremental | **Medio** | **Alta** | Diseñar esquema SQLite con las necesidades del roadmap |
| 4 | `from rich import print` sobrescribe `print()` built-in | **Bajo** | **Media** | Cambiar a `from rich.console import Console` y usar `console.print()` |
| 5 | `os.system("pause")` no es multiplataforma | **Bajo** | **Alta** | Reemplazar con `input("Presiona Enter para salir...")` |

---

## Recomendaciones inmediatas

**Máximo 5 acciones de alto impacto y bajo riesgo:**

1. **Crear estructura de paquetes:** separar en `scanner.py`, `duplicator.py`, `exporter.py`, `ui.py`, `config.py`. No agregar funcionalidad nueva hasta que esta separación esté lista.

2. **Agregar hashing SHA256:** es la mejora más crítica. Sin hashing, la herramienta no resuelve su problema real. Dos fases: (a) comparación por tamaño primero (rápido), (b) SHA256 solo de grupos con mismo tamaño.

3. **Diseñar esquema SQLite desde ahora:** tablas de `archivos`, `escaneos`, `grupos_duplicados`. No esperar a que el proyecto crezca para hacerlo.

4. **Configurar linting y formatting:** `ruff check` + `ruff format` en `pyproject.toml`. 5 minutos de setup, previene toda la deuda de estilo futura.

5. **Escribir un README mínimo:** qué hace, cómo se usa, requisitos. Un archivo markdown de 20 líneas que permita a cualquier persona entender el proyecto en 30 segundos.

---

## Lo que se descarta explícitamente (del alcance del proyecto)

- IA / detección de contenido inteligente
- Streaming / transcodificación
- Metadatos online (IMDb, MusicBrainz, etc.)
- Carátulas / portadas
- Servidor web / API REST
- App móvil
- Sincronización con la nube
- Bases de datos remotas (PostgreSQL, MySQL, etc.)
- GUI compleja (tkinter, PyQt, etc.)
- Soporte de formatos de imagen (solo video)

> **Regla:** si no está en la lista de "tecnologías excluidas" y no ayuda a encontrar duplicados, preguntar antes de agregar.

"""Modulo de base de datos SQLite para persistencia entre sesiones.

Tablas:
  - escaneos: metadatos de cada escaneo ejecutado
  - archivos: archivos individuales encontrados en cada escaneo
  - grupos_duplicados: grupos de duplicados detectados

Funciones principales:
  - guardar_escaneo: persistir resultados de un escaneo completo
  - obtener_escaneos: listar todos los escaneos guardados
  - obtener_ultimos_n: obtener los ultimos N escaneos
  - comparar_escaneos: comparar dos escaneos para detectar cambios
  - obtener_duplicados: recuperar duplicados de un escaneo
  - eliminar_escaneo: borrar un escaneo y sus datos asociados
"""

import json
import logging
import os
import pathlib
import sqlite3
import sys
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def _get_default_db_path() -> str:
    """Retorna la ruta por defecto a la base de datos.

    Prioridad de busqueda:
      1. Variable de entorno DETECTOR_DB_PATH
      2. XDG_DATA_HOME (Linux/Mac) o AppData (Windows)
      3. Fallback a directorio actual (para desarrollo local)

    Siempre crea el directorio padre antes de retornar la ruta.
    """
    # 1. Prioridad absoluta: variable de entorno
    db_env = os.environ.get("DETECTOR_DB_PATH")
    if db_env:
        # Asegurar que el directorio padre existe
        parent = pathlib.Path(db_env).parent
        parent.mkdir(parents=True, exist_ok=True)
        return db_env

    # 2. Prioridad estandar (XDG / AppData)
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            data_dir = pathlib.Path(appdata) / "DetectorDuplicados"
        else:
            local_path = os.path.join(os.path.expanduser("~"), "AppData", "Local")
            data_dir = pathlib.Path(local_path) / "DetectorDuplicados"
    else:
        # Linux / Mac
        xdg = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        data_dir = pathlib.Path(xdg) / "detector_duplicados"

    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "detector.db")


def create_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Crea y retorna una conexion a la base de datos SQLite.

    Args:
        db_path: Ruta al archivo SQLite. Si None, usa el valor por defecto.

    Returns:
        Objeto sqlite3.Connection con row_factory configurado.

    Raises:
        sqlite3.DatabaseError: Si la DB esta corrupta, muestra un
            mensaje amigable y retorna None (sin crash).
    """
    if db_path is None:
        db_path = _get_default_db_path()

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Verificar que la DB no este corrupta con un PRAGMA quick
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if integrity and integrity[0] != "ok":
            print(
                "\n[red]⚠️  La base de datos parece corrupta.[/]\n"
                "  Ruta: [path]{}[/]\n"
                "  Detalle: {}"
                "\n[red]Se intentara una reparacion automatica...[/]\n".format(
                    db_path, integrity[0]
                )
            )
            # Intentar reparacion: renombrar y crear nueva
            backup_path = db_path + ".corrupt"
            try:
                os.rename(db_path, backup_path)
                print(
                    f"[green]✅ DB original renombrada a {backup_path}[/]\n"
                    "[green]✅ Nueva base de datos creada.[/]\n"
                    "[yellow]Perdida de datos: los escaneos anteriores no se podran recuperar.[/]"
                )
            except OSError as e:
                print(
                    f"[red]❌ No se pudo renombrar la DB corrupta: {e}[/]\n"
                    "[yellow]Por favor elimine o mueva el archivo manualmente.[/]"
                )
                raise
            # Re-conectar con la nueva DB
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.DatabaseError as e:
        print(
            f"\n[red]⚠️  Error de base de datos:[/]\n"
            f"  Ruta: [path]{db_path}[/]\n"
            f"  Detalle: {e}\n"
            "[yellow]Por favor elimine o mueva el archivo y vuelva a intentarlo.[/]"
        )
        raise


def create_tables(conn: sqlite3.Connection) -> None:
    """Crea las tablas si no existen.

    Tablas:
        escaneos: metadatos de cada escaneo
        archivos: archivos individuales
        grupos_duplicados: grupos de duplicados
    """
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS escaneos (
            id INTEGER PRIMARY KEY,
            fecha TEXT NOT NULL,
            rutas TEXT NOT NULL,
            total_archivos INTEGER DEFAULT 0,
            total_carpetas INTEGER DEFAULT 0,
            modo TEXT DEFAULT 'rapido',
            duracion_ms INTEGER
        );

        CREATE TABLE IF NOT EXISTS archivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escaneo_id INTEGER NOT NULL REFERENCES escaneos(id) ON DELETE CASCADE,
            ruta TEXT NOT NULL,
            nombre TEXT NOT NULL,
            extension TEXT,
            tamanio_bytes INTEGER,
            hash_sha256 TEXT,
            hash_computado INTEGER DEFAULT 0,
            UNIQUE(escaneo_id, ruta)
        );

        CREATE TABLE IF NOT EXISTS grupos_duplicados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_sha256 TEXT,
            tamanio_bytes INTEGER,
            cantidad INTEGER,
            escaneo_id INTEGER NOT NULL REFERENCES escaneos(id) ON DELETE CASCADE,
            confirmado INTEGER DEFAULT 0,
            creado TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_archivos_hash
            ON archivos(escaneo_id, hash_sha256);

        CREATE INDEX IF NOT EXISTS idx_archivos_ruta
            ON archivos(escaneo_id, ruta);

        CREATE TABLE IF NOT EXISTS log_acciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,          -- 'mover', 'eliminar', 'renombrar', 'copiar'
            archivo_origen TEXT NOT NULL,
            archivo_destino TEXT,
            escaneo_id INTEGER,
            usuario TEXT,
            exito INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_log_acciones_tipo
            ON log_acciones(tipo);

        CREATE INDEX IF NOT EXISTS idx_log_acciones_fecha
            ON log_acciones(fecha DESC);
    """)


def guardar_escaneo(
    conn: sqlite3.Connection,
    rutas: list[str],
    total_archivos: int,
    total_carpetas: int,
    modo: str = "rapido",
    duracion_ms: int | None = None,
) -> int:
    """Guarda los metadados de un escaneo en la base de datos.

    Args:
        conn:Conexion a la base de datos.
        rutas: Lista de rutas escaneadas.
        total_archivos: Numero de archivos encontrados.
        total_carpetas: Numero de carpetas encontradas.
        modo: 'rapido' o 'preciso'.
        duracion_ms: Duracion del escaneo en milisegundos.

    Returns:
        El id del escaneo creado.
    """
    cursor = conn.execute(
        """INSERT INTO escaneos
           (fecha, rutas, total_archivos, total_carpetas, modo, duracion_ms)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(UTC).isoformat(),
            json.dumps(rutas),
            total_archivos,
            total_carpetas,
            modo,
            duracion_ms,
        ),
    )
    conn.commit()
    return cursor.lastrowid if cursor.lastrowid else 0


def guardar_archivos(
    conn: sqlite3.Connection,
    escaneo_id: int,
    archivos: list[dict[str, Any]],
) -> None:
    """Guarda los archivos de un escaneo en la base de datos.

    Args:
        conn: Conexion a la base de datos.
        escaneo_id: ID del escaneo al que pertenecen los archivos.
        archivos: Lista de dicts con claves 'ruta', 'nombre', 'extension',
                  'tamanio', 'mtime', 'hash_sha256' (opcional),
                  'hash_computado' (opcional).
    """
    rows = []
    for a in archivos:
        rows.append(
            (
                escaneo_id,
                a["ruta"],
                a["nombre"],
                a.get("extension"),
                a.get("tamanio"),
                a.get("hash_sha256"),
                a.get("hash_computado", 0),
            )
        )

    conn.executemany(
        """INSERT OR REPLACE INTO archivos
           (escaneo_id, ruta, nombre, extension, tamanio_bytes,
            hash_sha256, hash_computado)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()


def guardar_grupos_duplicados(
    conn: sqlite3.Connection,
    escaneo_id: int,
    confirmados: dict,
    sospechosos: dict,
) -> None:
    """Guarda los grupos de duplicados en la base de datos.

    Args:
        conn: Conexion a la base de datos.
        escaneo_id: ID del escaneo.
        confirmados: Dict con clave=hash_sha256, valor=[list de rutas].
        sospechosos: Dict con clave=nombre, valor=[list de rutas].
    """
    now = datetime.now(UTC).isoformat()

    for h, rutas in confirmados.items():
        # Obtener tamanio de uno de los archivos del grupo
        tamanio = None
        for r in rutas:
            fila = conn.execute(
                "SELECT tamanio_bytes FROM archivos WHERE escaneo_id=? AND ruta=?",
                (escaneo_id, r),
            ).fetchone()
            if fila:
                tamanio = fila["tamanio_bytes"]
                break

        conn.execute(
            """INSERT INTO grupos_duplicados
               (hash_sha256, tamanio_bytes, cantidad, escaneo_id, confirmado, creado)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (h, tamanio or 0, len(rutas), escaneo_id, now),
        )

    for _nombre, rutas in sospechosos.items():
        # Intentar obtener tamanio desde la tabla archivos
        tamanio = None
        for r in rutas:
            fila = conn.execute(
                "SELECT tamanio_bytes FROM archivos WHERE escaneo_id=? AND ruta=?",
                (escaneo_id, r),
            ).fetchone()
            if fila:
                tamanio = fila["tamanio_bytes"]
                break

        conn.execute(
            """INSERT INTO grupos_duplicados
               (hash_sha256, tamanio_bytes, cantidad, escaneo_id, confirmado, creado)
               VALUES (NULL, ?, ?, ?, 0, ?)""",
            (tamanio, len(rutas), escaneo_id, now),
        )

    conn.commit()


def obtener_escaneos(
    conn: sqlite3.Connection,
    limit: int = 50,
) -> list[sqlite3.Row]:
    """Retorna todos los escaneos, ordenados por fecha descendente.

    Args:
        conn: Conexion a la base de datos.
        limit: Maximo de resultados a retornar.

    Returns:
        Lista de sqlite3.Row con los campos de la tabla escaneos.
    """
    cursor = conn.execute(
        "SELECT * FROM escaneos ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    return cursor.fetchall()


def obtener_escaneo(conn: sqlite3.Connection, escaneo_id: int) -> sqlite3.Row | None:
    """Retorna un escaneo por su ID.

    Args:
        conn: Conexion a la base de datos.
        escaneo_id: ID del escaneo.

    Returns:
        sqlite3.Row o None si no existe.
    """
    fila = conn.execute("SELECT * FROM escaneos WHERE id = ?", (escaneo_id,)).fetchone()
    return fila


def obtener_archivos_escaneo(
    conn: sqlite3.Connection,
    escaneo_id: int,
) -> list[dict[str, Any]]:
    """Retorna todos los archivos de un escaneo.

    Args:
        conn: Conexion a la base de datos.
        escaneo_id: ID del escaneo.

    Returns:
        Lista de dicts con informacion de los archivos.
    """
    cursor = conn.execute("SELECT * FROM archivos WHERE escaneo_id = ?", (escaneo_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def obtener_duplicados(
    conn: sqlite3.Connection,
    escaneo_id: int,
    confirmado: int | None = None,
) -> list[dict[str, Any]]:
    """Retorna los grupos de duplicados de un escaneo.

    Args:
        conn: Conexion a la base de datos.
        escaneo_id: ID del escaneo.
        confirmado: Si None, retorna todos. 1=confirmados, 0=sospechosos.

    Returns:
        Lista de dicts con informacion de los grupos de duplicados.
    """
    query = """
        SELECT gd.*,
               (SELECT GROUP_CONCAT(ruta, '; ')
                FROM archivos a
                WHERE a.escaneo_id = gd.escaneo_id
                  AND (gd.hash_sha256 IS NULL OR a.hash_sha256 = gd.hash_sha256)
               ) as rutas
        FROM grupos_duplicados gd
        WHERE gd.escaneo_id = ?
    """
    params: list[Any] = [escaneo_id]

    if confirmado is not None:
        query += " AND gd.confirmado = ?"
        params.append(confirmado)

    query += " ORDER BY gd.cantidad DESC"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def comparar_escaneos(
    conn: sqlite3.Connection,
    id1: int,
    id2: int,
) -> dict[str, list[dict[str, Any]]]:
    """Compara dos escaneos y retorna cambios.

    Detecta:
        - nuevos: archivos presentes en el escaneo2 pero no en el 1
        - eliminados: archivos presentes en el 1 pero no en el 2
        - movidos: archivos con mismo hash pero diferente ruta
        - duplicados_nuevos: grupos de duplicados que aparecieron en el escaneo2

    Args:
        conn: Conexion a la base de datos.
        id1: ID del primer escaneo.
        id2: ID del segundo escaneo.

    Returns:
        Dict con claves: 'nuevos', 'eliminados', 'movidos', 'duplicados_nuevos'.
    """
    # Obtener hashes de cada escaneo
    esc1_files = conn.execute(
        "SELECT ruta, hash_sha256 FROM archivos WHERE escaneo_id = ?", (id1,)
    ).fetchall()

    esc2_files = conn.execute(
        "SELECT ruta, hash_sha256 FROM archivos WHERE escaneo_id = ?", (id2,)
    ).fetchall()

    esc1_rutas = set(row["ruta"] for row in esc1_files)
    esc2_rutas = set(row["ruta"] for row in esc2_files)

    esc1_hashes: dict[str, str | None] = {}
    for row in esc1_files:
        if row["hash_sha256"]:
            esc1_hashes[row["hash_sha256"]] = row["ruta"]

    esc2_hashes: dict[str, str | None] = {}
    for row in esc2_files:
        if row["hash_sha256"]:
            esc2_hashes[row["hash_sha256"]] = row["ruta"]

    # Nuevos y eliminados
    nuevos_rutas = esc2_rutas - esc1_rutas
    eliminados_rutas = esc1_rutas - esc2_rutas

    nuevos = [{"ruta": r} for r in sorted(nuevos_rutas)]
    eliminados = [{"ruta": r} for r in sorted(eliminados_rutas)]

    # Movidos: mismo hash, diferente ruta
    movidos: list[dict] = []
    for h in set(esc1_hashes.keys()) & set(esc2_hashes.keys()):
        r1 = esc1_hashes[h]
        r2 = esc2_hashes[h]
        if r1 != r2 and r2 in nuevos_rutas and r1 in eliminados_rutas:
            movidos.append(
                {
                    "hash": h,
                    "ruta_antigua": r1,
                    "ruta_nueva": r2,
                }
            )

    # Nuevos duplicados
    dup_old = conn.execute(
        "SELECT hash_sha256, tamanio_bytes, cantidad, confirmado "
        "FROM grupos_duplicados WHERE escaneo_id = ?",
        (id1,),
    ).fetchall()

    dup_new = conn.execute(
        "SELECT hash_sha256, tamanio_bytes, cantidad, confirmado "
        "FROM grupos_duplicados WHERE escaneo_id = ?",
        (id2,),
    ).fetchall()

    set_old_hashes = set(row["hash_sha256"] for row in dup_old if row["hash_sha256"])

    duplicados_nuevos = [
        dict(row)
        for row in dup_new
        if row["hash_sha256"] and row["hash_sha256"] not in set_old_hashes
    ]

    return {
        "nuevos": nuevos,
        "eliminados": eliminados,
        "movidos": movidos,
        "duplicados_nuevos": duplicados_nuevos,
    }


def eliminar_escaneo(conn: sqlite3.Connection, escaneo_id: int) -> bool:
    """Elimina un escaneo y todos sus datos asociados.

    Args:
        conn: Conexion a la base de datos.
        escaneo_id: ID del escaneo a eliminar.

    Returns:
        True si se elimino, False si no existe.
    """
    result = conn.execute("DELETE FROM escaneos WHERE id = ?", (escaneo_id,)).rowcount
    if result > 0:
        conn.commit()
        return True
    return False


def escaneo_existe(conn: sqlite3.Connection, ruta: str) -> bool:
    """Verifica si ya existe un escaneo que contenga una ruta dada.

    Args:
        conn: Conexion a la base de datos.
        ruta: Ruta a buscar.

    Returns:
        True si algun escaneo contiene esta ruta.
    """
    resultado = conn.execute("SELECT rutas FROM escaneos").fetchall()

    for row in resultado:
        escaneadas: list = json.loads(row["rutas"])
        if ruta in escaneadas:
            return True
    return False


def obtener_espacio_usado(conn: sqlite3.Connection) -> dict[str, Any]:
    """Retorna estadisticas de uso de la base de datos.

    Returns:
        Dict con 'tamano_archivo', 'total_escaneos', 'total_archivos',
        'total_duplicados', 'espacio_duplicado_bytes'.
    """
    tamano = os.path.getsize(conn.execute("PRAGMA database_list").fetchone()[2])

    total_escaneos = conn.execute("SELECT COUNT(*) FROM escaneos").fetchone()[0]
    total_archivos = conn.execute("SELECT COUNT(*) FROM archivos").fetchone()[0]
    total_duplicados = conn.execute(
        "SELECT COUNT(*) FROM grupos_duplicados WHERE confirmado = 1"
    ).fetchone()[0]

    espacio_duplicado = conn.execute(
        "SELECT COALESCE(SUM(tamanio_bytes), 0) FROM grupos_duplicados WHERE confirmado = 1"
    ).fetchone()[0]

    return {
        "tamano_archivo": tamano,
        "total_escaneos": total_escaneos,
        "total_archivos": total_archivos,
        "total_duplicados": total_duplicados,
        "espacio_duplicado_bytes": espacio_duplicado,
    }


def registrar_accion(
    conn: sqlite3.Connection,
    tipo: str,
    archivo_origen: str,
    archivo_destino: str | None = None,
    escaneo_id: int | None = None,
    exito: bool = True,
) -> None:
    """Registra una accion en el log de acciones.

    Args:
        conn: Conexion a la base de datos.
        tipo: Tipo de accion ('mover', 'eliminar', 'renombrar', 'copiar').
        archivo_origen: Ruta del archivo original.
        archivo_destino: Ruta destino (si aplica).
        escaneo_id: ID del escaneo asociado.
        exito: True si la accion fue exitosa, False si fallo.
    """
    conn.execute(
        """INSERT INTO log_acciones
           (fecha, tipo, archivo_origen, archivo_destino, escaneo_id, exito)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(UTC).isoformat(),
            tipo,
            archivo_origen,
            archivo_destino,
            escaneo_id,
            1 if exito else 0,
        ),
    )
    conn.commit()


def deshacer_accion(conn: sqlite3.Connection, accion_id: int) -> bool:
    """Deshace una accion registrada en el log.

    Args:
        conn: Conexion a la base de datos.
        accion_id: ID de la accion a deshacer.

    Returns:
        True si se desho, False si no se encontro o es irreversible.
    """
    accion = conn.execute("SELECT * FROM log_acciones WHERE id = ?", (accion_id,)).fetchone()

    if not accion:
        return False

    if accion["tipo"] not in ("mover", "renombrar"):
        return False  # Eliminar y copiar son irreversibles por ahora

    # Intentar deshacer moviendo el archivo de nuevo
    origen = accion["archivo_origen"]
    destino = accion["archivo_destino"]

    if not destino:
        return False

    try:
        if os.path.exists(destino):
            import shutil

            shutil.move(destino, origen)
            return True
        else:
            return False
    except Exception:
        return False


def obtener_rollback_disponible(
    conn: sqlite3.Connection,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retorna las ultimas N acciones que pueden ser deshechas.

    Args:
        conn: Conexion a la base de datos.
        limit: Maximo de resultados a retornar.

    Returns:
        Lista de dicts con informacion de las acciones reversibles.
    """
    cursor = conn.execute(
        """SELECT * FROM log_acciones
           WHERE tipo IN ('mover', 'renombrar') AND exito = 1
           ORDER BY id DESC LIMIT ?""",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]

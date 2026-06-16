"""Módulo de exportación de resultados (Fase 3).

Soporta exportación a TXT plano, CSV y JSON.
"""

import csv
import json

from .config import COLOR_ERROR, COLOR_OK
from .theme import console


def guardar_resultados_txt(
    duplicados: dict, nombre_archivo: str = "duplicados_encontrados.txt"
) -> bool:
    """Guarda los resultados en un archivo TXT plano.

    Equivalente a guardar_resultados_txt() del script original.

    Args:
        duplicados: Dict con claves 'archivos_duplicados' y 'carpetas_duplicadas'.
        nombre_archivo: Ruta del archivo de salida.

    Returns:
        True si se guardó exitosamente, False si hubo error.
    """
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write("=== ARCHIVOS DUPLICADOS ===\n\n")

            if duplicados["archivos_duplicados"]:
                for nombre, rutas in duplicados["archivos_duplicados"].items():
                    f.write(f"{nombre}\n")
                    for ruta in rutas:
                        f.write(f" - {ruta}\n")
                    f.write("\n")
            else:
                f.write("No se encontraron archivos duplicados.\n\n")

            f.write("=== CARPETAS DUPLICADAS ===\n\n")

            if duplicados["carpetas_duplicadas"]:
                for nombre, rutas in duplicados["carpetas_duplicadas"].items():
                    f.write(f"{nombre}\n")
                    for ruta in rutas:
                        f.write(f" - {ruta}\n")
                    f.write("\n")
            else:
                f.write("No se encontraron carpetas duplicadas.\n\n")

        console.print(f"\n[{COLOR_OK}] Archivo de resultados guardado como: {nombre_archivo}")
        return True

    except Exception as e:
        console.print(f"\n[{COLOR_ERROR}] Error al guardar el archivo TXT: {e}")
        return False


def exportar_resultados(
    detalle: dict,
    escaneo_id: int,
    nombre_archivo: str | None = None,
    formato: str = "txt",
) -> bool:
    """Exporta los resultados de un escaneo a un archivo.

    Args:
        detalle: Dict con claves 'escaneo', 'archivos', 'duplicados'.
        escaneo_id: ID del escaneo exportado.
        nombre_archivo: Ruta del archivo de salida. Si None, genera automatico.
        formato: Formato de exportacion ('txt', 'csv', 'json').

    Returns:
        True si se exporto exitosamente.
    """
    if nombre_archivo is None:
        ext_map = {"txt": "txt", "csv": "csv", "json": "json"}
        ext = ext_map.get(formato, "txt")
        nombre_archivo = f"duplicados_escaneo_{escaneo_id}.{ext}"

    try:
        escaneo = detalle["escaneo"]
        duplicados = detalle["duplicados"]

        if formato == "txt":
            _exportar_txt(escaneo, duplicados, nombre_archivo)
        elif formato == "csv":
            _exportar_csv(escaneo, duplicados, nombre_archivo)
        elif formato == "json":
            _exportar_json(escaneo, duplicados, nombre_archivo)
        else:
            console.print(f"[warning]Formato '{formato}' no soportado. Usando TXT.[/]")
            _exportar_txt(escaneo, duplicados, nombre_archivo)

        console.print(f"[green]Exportado a: {nombre_archivo}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]Error al exportar: {e}[/red]")
        return False


def _exportar_txt(escaneo: dict, duplicados: list, nombre_archivo: str) -> None:
    """Exporta a TXT (Fase 3)."""
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(f"=== ESCANEO #{escaneo['id']} ===\n")
        f.write(f"Fecha: {escaneo['fecha']}\n")
        f.write(f"Total archivos: {escaneo['total_archivos']}\n")
        f.write(f"Total carpetas: {escaneo['total_carpetas']}\n")
        f.write(f"Modo: {escaneo['modo']}\n")
        f.write(f"Total duplicados: {len(duplicados)}\n")
        f.write("=" * 50 + "\n\n")

        for dup in duplicados:
            f.write(f"[{'CONFIRMADO' if dup['confirmado'] else 'SOSPECHOSO'}]\n")
            if dup["hash_sha256"]:
                f.write(f"  Hash: {dup['hash_sha256']}\n")
            f.write(f"  Tamanio: {dup['tamanio_bytes']} bytes\n")
            f.write(f"  Cantidad: {dup['cantidad']}\n")
            f.write("  Rutas:\n")
            rutas = dup.get("rutas", "").split("; ") if dup.get("rutas") else []
            for ruta in rutas:
                f.write(f"    - {ruta}\n")
            f.write("\n")


def _exportar_csv(escaneo: dict, duplicados: list, nombre_archivo: str) -> bool:
    """Exporta a CSV (Fase 3).

    Args:
        escaneo: Dict con metadatos del escaneo.
        duplicados: Lista de grupos de duplicados.
        nombre_archivo: Ruta del archivo CSV.

    Returns:
        True si se exporto exitosamente.
    """
    try:
        with open(nombre_archivo, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Grupo", "Tipo", "Hash", "Tamano", "Cantidad", "Ruta"])

            grupo_num = 1
            for dup in duplicados:
                tipo = "CONFIRMADO" if dup["confirmado"] else "SOSPECHOSO"
                hash_val = dup.get("hash_sha256", "N/A") or "N/A"
                tamanio = dup.get("tamanio_bytes", 0) or 0
                cantidad = dup.get("cantidad", 0) or 0
                rutas = dup.get("rutas", "").split("; ") if dup.get("rutas") else []

                for ruta in rutas:
                    writer.writerow([grupo_num, tipo, hash_val, tamanio, cantidad, ruta])

                grupo_num += 1

        return True
    except Exception as e:
        console.print(f"[red]Error al exportar CSV: {e}[/red]")
        return False


def _exportar_json(escaneo: dict, duplicados: list, nombre_archivo: str) -> bool:
    """Exporta a JSON (Fase 3).

    Args:
        escaneo: Dict con metadatos del escaneo.
        duplicados: Lista de grupos de duplicados.
        nombre_archivo: Ruta del archivo JSON.

    Returns:
        True si se exporto exitosamente.
    """
    try:
        data = {
            "escaneo": {
                "id": escaneo["id"],
                "fecha": escaneo["fecha"],
                "rutas": escaneo.get("rutas", []),
                "total_archivos": escaneo["total_archivos"],
                "total_carpetas": escaneo["total_carpetas"],
                "modo": escaneo["modo"],
            },
            "duplicados": duplicados,
        }

        with open(nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        console.print(f"[red]Error al exportar JSON: {e}[/red]")
        return False

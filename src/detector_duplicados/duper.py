"""Motor de detección de duplicados.

Detección dual:
  1. Hash SHA256 → duplicados confirmados (verdad única)
  2. Mismo nombre + tamaño → sospechosos (no confirmados)

Criterio de confianza configurable.
"""


def encontrar_duplicados(
    archivos: list[dict[str, str | int]],
    carpetas: list[dict[str, str]],
    confirmar_por_hash: bool = False,
) -> tuple[dict, dict, int, int]:
    """Detecta archivos y carpetas duplicados.

    Args:
        archivos: Lista de dicts con 'nombre', 'extension', 'ruta',
                  'tamanio', 'mtime'.
        carpetas: Lista de dicts con 'nombre', 'ruta'.
        confirmar_por_hash: Si True, usa SHA256 para confirmar duplicados
                           (solo de archivos que comparten tamaño).

    Returns:
        (duplicados_confirmados, sospechosos, total_confirmados, total_sospechosos)
    """
    # --- Detección por hash (primera línea) ---
    duplicados_confirmados: dict = {}

    if confirmar_por_hash:
        from .scanner import agrupar_por_tamanio, calcular_hash_grupo

        grupos = agrupar_por_tamanio(archivos)
        if grupos:
            print(f"\n[#00FF41] Calculando hashes de {len(grupos)} grupo(s) de mismo tamaño...")
            for _tam, archivos_con_tam in grupos.items():
                hashes = calcular_hash_grupo(archivos_con_tam)
                hash_groups: dict[str, list[str]] = {}
                for ruta, h in hashes.items():
                    if h is None:
                        continue
                    if h not in hash_groups:
                        hash_groups[h] = []
                    hash_groups[h].append(ruta)

                for h, rutas in hash_groups.items():
                    if len(rutas) > 1:
                        # Incluir metadata del archivo para compatibilidad con UI
                        info_base = None
                        for a in archivos_con_tam:
                            if a["ruta"] == rutas[0]:
                                info_base = a
                                break
                        duplicados_confirmados[h] = {
                            "rutas": rutas,
                            "tamanio": info_base.get("tamanio", 0) if info_base else 0,
                            "hash": h,
                        }

    # --- Detección por nombre (segunda línea: sospechosos) ---
    sospechosos: dict = {}

    archivos_temp: dict[str, list[dict]] = {}
    for archivo in archivos:
        clave = archivo["nombre"].lower().strip()
        if clave not in archivos_temp:
            archivos_temp[clave] = []
        archivos_temp[clave].append(archivo)

    for nombre, archivos_con_nombre in archivos_temp.items():
        if len(archivos_con_nombre) > 1:
            rutas = [a["ruta"] for a in archivos_con_nombre]
            sospechosos[nombre] = rutas

    # --- Carpetas duplicadas (siempre por nombre) ---
    carpetas_temp: dict[str, list[str]] = {}
    for carpeta in carpetas:
        clave = carpeta["nombre"].lower().strip()
        if clave not in carpetas_temp:
            carpetas_temp[clave] = [carpeta["ruta"]]
        else:
            carpetas_temp[clave].append(carpeta["ruta"])

    carpetas_duplicadas = {
        nombre: rutas for nombre, rutas in carpetas_temp.items() if len(rutas) > 1
    }

     # Fusionar carpetas duplicadas con sospechosos (ambos son "no confirmados")
    sospechosos.update(carpetas_duplicadas)

    def _count_rutas(item: dict | list) -> int:
        if isinstance(item, dict):
            return len(item.get("rutas", []))
        return len(item)

    total_confirmados = sum(_count_rutas(v) for v in duplicados_confirmados.values())
    total_sospechosos = len(sospechosos)

    return duplicados_confirmados, sospechosos, total_confirmados, total_sospechosos

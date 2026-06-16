"""Motor de politicas de conservacion para cleanup.

Cada politica define reglas sobre que archivos duplicados
se pueden eliminar y cuales deben mantenerse siempre.

Políticas implementadas:
  - "keep_one_copy": Mantener siempre al menos 1 copia
  - "keep_newest": Mantener siempre la copia mas reciente
  - "keep_oldest": Mantener siempre la copia mas antigua
  - "keep_in_path": Mantener copias en rutas especificas
  - "aggressive": Eliminar todo excepto 1 copia de cada grupo
  - "conservative": Solo eliminar si hay >= 3 copias
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PolicyError(Exception):
    """Error lanzado cuando una politica no se puede aplicar."""

    pass


class DuplicadoPolicy:
    """Clase base para politicas de conservacion."""

    name: str = "base"

    def apply(self, grupo: dict) -> dict:
        """Aplica la politica a un grupo de duplicados.

        Args:
            grupo: Dict con claves:
                - "id": ID del grupo duplicado
                - "rutas": Lista de rutas de archivos duplicados
                - "tamanio": Tamano en bytes (de cada archivo)
                - "hash": Hash SHA256
                - "escaneo_id": ID del escaneo asociado

        Returns:
            Dict con:
                - "accion": str - tipo de accion sugerida
                - "eliminar": list[str] - rutas a eliminar
                - "mantener": list[str] - rutas a mantener
                - "motivo": str - explicacion de la decision
        """
        raise NotImplementedError


class KeepOneCopyPolicy(DuplicadoPolicy):
    """Mantiene siempre al menos 1 copia de cada grupo."""

    name = "keep_one_copy"

    def apply(self, grupo: dict) -> dict:
        rutas = grupo.get("rutas", [])
        if len(rutas) <= 1:
            return {
                "accion": "ninguna",
                "eliminar": [],
                "mantener": rutas,
                "motivo": "Solo hay 1 archivo en este grupo.",
            }

        # Mantener el primero, eliminar el resto
        return {
            "accion": "eliminar",
            "eliminar": rutas[1:],
            "mantener": [rutas[0]],
            "motivo": f"Se mantiene 1 copia (primero), se eliminan {len(rutas) - 1} duplicados.",
        }


class KeepNewestPolicy(DuplicadoPolicy):
    """Mantiene siempre la copia mas reciente."""

    name = "keep_newest"

    def apply(self, grupo: dict) -> dict:
        rutas = grupo.get("rutas", [])
        if len(rutas) <= 1:
            return {
                "accion": "ninguna",
                "eliminar": [],
                "mantener": rutas,
                "motivo": "Solo hay 1 archivo en este grupo.",
            }

        # Obtener mtime de cada archivo
        mtimes = []
        for ruta in rutas:
            try:
                import os

                mtime = os.path.getmtime(ruta)
                mtimes.append((ruta, mtime))
            except OSError:
                mtimes.append((ruta, 0))

        # Ordenar por mtime (mas reciente primero)
        mtimes.sort(key=lambda x: x[1], reverse=True)

        return {
            "accion": "eliminar",
            "eliminar": [r for r, m in mtimes[1:]],
            "mantener": [mtimes[0][0]],
            "motivo": f"Se mantiene la copia mas reciente ({datetime.fromtimestamp(mtimes[0][1]).strftime('%Y-%m-%d')}), se eliminan {len(mtimes) - 1} copias antiguas.",  # noqa: E501
        }


class KeepOldestPolicy(DuplicadoPolicy):
    """Mantiene siempre la copia mas antigua."""

    name = "keep_oldest"

    def apply(self, grupo: dict) -> dict:
        rutas = grupo.get("rutas", [])
        if len(rutas) <= 1:
            return {
                "accion": "ninguna",
                "eliminar": [],
                "mantener": rutas,
                "motivo": "Solo hay 1 archivo en este grupo.",
            }

        # Obtener mtime de cada archivo
        mtimes = []
        for ruta in rutas:
            try:
                import os

                mtime = os.path.getmtime(ruta)
                mtimes.append((ruta, mtime))
            except OSError:
                mtimes.append((ruta, 0))

        # Ordenar por mtime (mas antiguo primero)
        mtimes.sort(key=lambda x: x[1])

        return {
            "accion": "eliminar",
            "eliminar": [r for r, m in mtimes[1:]],
            "mantener": [mtimes[0][0]],
            "motivo": f"Se mantiene la copia mas antigua ({datetime.fromtimestamp(mtimes[0][1]).strftime('%Y-%m-%d')}), se eliminan {len(mtimes) - 1} copias recientes.",  # noqa: E501
        }


class KeepInPathPolicy(DuplicadoPolicy):
    """Mantiene copias en rutas especificas."""

    def __init__(self, rutas_protegidas: list[str]):
        """Inicializa con rutas protegidas.

        Args:
            rutas_protegidas: Lista de rutas que nunca deben eliminarse.
        """
        self.rutas_protegidas = rutas_protegidas
        self.name = "keep_in_path"

    def apply(self, grupo: dict) -> dict:
        rutas = grupo.get("rutas", [])

        # Filtrar rutas protegidas
        rutas_seguras = []
        rutas_inseguras = []

        for ruta in rutas:
            if any(ruta.startswith(p) for p in self.rutas_protegidas):
                rutas_seguras.append(ruta)
            else:
                rutas_inseguras.append(ruta)

        if not rutas_inseguras:
            return {
                "accion": "ninguna",
                "eliminar": [],
                "mantener": rutas,
                "motivo": "Todas las copias estan en rutas protegidas.",
            }

        # Mantener las protegidas, eliminar las demas
        return {
            "accion": "eliminar",
            "eliminar": rutas_inseguras,
            "mantener": rutas_seguras,
            "motivo": f"Se mantienen {len(rutas_seguras)} copias en rutas protegidas, se eliminan {len(rutas_inseguras)} en rutas no protegidas."  # noqa: E501
        }


class AggressivePolicy(DuplicadoPolicy):
    """Elimina todo excepto 1 copia de cada grupo (maximo riesgo)."""

    name = "aggressive"

    def apply(self, grupo: dict) -> dict:
        return KeepOneCopyPolicy().apply(grupo)


class ConservativePolicy(DuplicadoPolicy):
    """Solo elimina si hay >= 3 copias."""

    name = "conservative"

    def apply(self, grupo: dict) -> dict:
        rutas = grupo.get("rutas", [])
        if len(rutas) < 3:
            return {
                "accion": "ninguna",
                "eliminar": [],
                "mantener": rutas,
                "motivo": "Solo hay 2 copias (menos del minimo de 3).",
            }

        return KeepOneCopyPolicy().apply(grupo)


def aplicar_politica(
    grupo: dict,
    politica: str,
    rutas_protegidas: list[str] | None = None,
) -> dict:
    """Aplica una politica a un grupo de duplicados.

    Args:
        grupo: Dict con informacion del grupo duplicado.
        politica: Nombre de la politica a aplicar.
        rutas_protegidas: Rutas que nunca deben eliminarse (para keep_in_path).

    Returns:
        Dict con accion, eliminar, mantener, motivo.

    Raises:
        PolicyError: Si la politica no existe o no se puede aplicar.
    """
    rutas_protegidas = rutas_protegidas or []

    politicas = {
        "keep_one_copy": KeepOneCopyPolicy,
        "keep_newest": KeepNewestPolicy,
        "keep_oldest": KeepOldestPolicy,
        "keep_in_path": lambda: KeepInPathPolicy(rutas_protegidas),
        "aggressive": AggressivePolicy,
        "conservative": ConservativePolicy,
    }

    if politica not in politicas:
        raise PolicyError(f"Politica '{politica}' no existe. Opciones: {list(politicas.keys())}")

    policy_instance = politicas[politica]()
    resultado = policy_instance.apply(grupo)

    # Asegurar que archivos protegidos nunca se eliminan
    if rutas_protegidas and resultado["eliminar"]:
        protegidos = [
            r for r in resultado["eliminar"] if any(r.startswith(p) for p in rutas_protegidas)
        ]
        if protegidos:
            resultado["mantener"].extend(protegidos)
            resultado["eliminar"] = [
                r
                for r in resultado["eliminar"]
                if not any(r.startswith(p) for p in rutas_protegidas)
            ]
            if not resultado["eliminar"]:
                resultado["accion"] = "ninguna"
                resultado["motivo"] = "Todas las copias estan en rutas protegidas."

    return resultado


# Perfiles — fuente unica de verdad: config.py (PERFILES_PREDEFINIDOS)
# policies.py importa desde config para evitar duplicacion

# Re-export for backward compatibility
from .config import PERFILES_PREDEFINIDOS as PERFILES  # noqa: E402, F401

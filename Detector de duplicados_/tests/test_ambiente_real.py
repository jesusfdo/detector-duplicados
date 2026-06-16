"""Script para crear un entorno de prueba real con archivos y carpetas."""
import os
import random
import shutil
import string


def generar_nombre_carpeta():
    """Genera un nombre de carpeta realista."""
    nombres = [
        "Documentos", "Fotos", "Videos", "Musica", "Proyectos",
        "Descargas", "Trabajo", "Personal", "Backup", "Temp",
        "Imágenes", "Vídeos", "Áudio", "Escritorio", "Configuración",
    ]
    return random.choice(nombres) + f"_{random.randint(1, 99)}"


def generar_nombre_archivo(tipo="mixed"):
    """Genera un nombre de archivo realista."""
    nombres = {
        "txt": ["nota", "registro", "lista", "archivo", "documento", "reporte"],
        "jpg": ["foto", "imagen", "pantallazo", "captura", "recuerdo", "vacaciones"],
        "mp4": ["video", "pelicula", "tutorial", "grabacion", "clip", "documental"],
        "mp3": ["cancion", "musica", "podcast", "audiolibro", "tema", "melodia"],
        "pdf": ["manual", "guia", "especificacion", "contrato", "factura", "recibo"],
        "zip": ["backup", "comprimido", "archivo", "paquete", "distribucion", "instalador"],
        "doc": ["carta", "solicitud", "propuesta", "plan", "presupuesto", "orden"],
        "xlsx": ["datos", "tabla", "calculo", "presupuesto", "inventario", "contabilidad"],
    }

    ext = tipo if tipo != "mixed" else random.choice(list(nombres.keys()))
    nombre = random.choice(nombres[ext])
    numero = random.randint(1, 9999)
    return f"{nombre}_{numero}.{ext}"


def crear_entorno_prueba(ruta_base="/tmp/test_detector_duplicados"):
    """Crea un entorno de prueba completo con archivos y carpetas."""
    print(f"Creando entorno de prueba en: {ruta_base}")

    # Limpiar si existe
    if os.path.exists(ruta_base):
        shutil.rmtree(ruta_base)

    os.makedirs(ruta_base, exist_ok=True)

    # Estructura de carpetas realista
    carpetas = []
    for _i in range(20):  # 20 carpetas principales
        carpeta = os.path.join(ruta_base, generar_nombre_carpeta())
        os.makedirs(carpeta, exist_ok=True)
        carpetas.append(carpeta)

        # Subcarpetas (2-5 por carpeta principal)
        for _ in range(random.randint(2, 5)):
            subcarpeta = os.path.join(carpeta, generar_nombre_carpeta())
            os.makedirs(subcarpeta, exist_ok=True)
            carpetas.append(subcarpeta)

    print(f"  Creadas {len(carpetas)} carpetas")

    # Crear archivos con duplicados
    archivos_creados = []
    tipos_archivos = ["txt", "jpg", "mp4", "mp3", "pdf", "zip", "doc", "xlsx"]

    # Crear archivos unicos (no duplicados)
    print("  Creando archivos unicos...")
    for _ in range(500):
        carpeta = random.choice(carpetas)
        nombre = generar_nombre_archivo()
        ruta = os.path.join(carpeta, nombre)
        ext = os.path.splitext(nombre)[1][1:]
        contenido = ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=random.randint(100, 5000)))
        with open(ruta, 'w') as f:
            f.write(contenido)
        archivos_creados.append(ruta)

    # Crear archivos DUPLICADOS
    print("  Creando archivos DUPLICADOS...")
    num_duplicados = 150

    for _ in range(num_duplicados):
        carpeta_origen = random.choice(carpetas)
        nombre_origen = generar_nombre_archivo()
        ruta_origen = os.path.join(carpeta_origen, nombre_origen)

        # Asegurar que el archivo original exista
        if not os.path.exists(ruta_origen):
            contenido = ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=random.randint(100, 5000)))
            with open(ruta_origen, 'w') as f:
                f.write(contenido)

        # Leer el contenido original
        with open(ruta_origen, 'rb') as f:
            contenido_original = f.read()

        # Crear copias en otras carpetas
        num_copias = random.randint(2, 4)
        carpetas_destino = random.sample(
            [c for c in carpetas if c != carpeta_origen],
            min(num_copias, len(carpetas) - 1)
        )

        for destino in carpetas_destino:
            if random.random() < 0.7:
                nombre_destino = nombre_origen  # Mismo nombre = duplicado obvio
            else:
                nombre_destino = f"backup_{nombre_origen}"  # Nombre diferente

            ruta_destino = os.path.join(destino, nombre_destino)
            with open(ruta_destino, 'wb') as f:
                f.write(contenido_original)
            archivos_creados.append(ruta_destino)

    # Estadisticas
    total_size = 0
    num_archivos = 0
    for root, _dirs, files in os.walk(ruta_base):
        for file in files:
            total_size += os.path.getsize(os.path.join(root, file))
            num_archivos += 1

    print("\nEntorno de prueba creado:")
    print(f"  - {len(carpetas)} carpetas principales")
    print(f"  - {num_archivos} archivos totales")
    print(f"  - ~{num_duplicados} archivos con duplicados")
    print(f"  - Tamaño total: {total_size / 1024 / 1024:.2f} MB")

    return ruta_base


if __name__ == "__main__":
    crear_entorno_prueba()

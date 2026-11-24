"""
Configuración del archivo de logs del sistema Software FJ.

Todos los eventos relevantes y todos los errores se escriben en
logs/software_fj.log, sin necesidad de base de datos.
"""

import logging  # módulo estándar de Python para registrar eventos
from pathlib import Path  # manejo de rutas independiente del sistema operativo

# Carpeta "logs" ubicada en la raíz del proyecto (un nivel arriba de este archivo).
RUTA_LOGS = Path(__file__).resolve().parent.parent / "logs"
# Ruta completa del archivo donde se guardan los registros.
ARCHIVO_LOG = RUTA_LOGS / "software_fj.log"


def configurar_logger(nombre: str = "software_fj") -> logging.Logger:
    """Crea (una sola vez) el logger del sistema y lo devuelve."""
    # Se obtiene el logger por nombre; si ya existe, Python devuelve el mismo.
    logger = logging.getLogger(nombre)
    # Si ya tiene manejadores, se devuelve tal cual para no duplicar líneas.
    if logger.handlers:
        return logger
    # Se registra todo desde el nivel DEBUG hacia arriba.
    logger.setLevel(logging.DEBUG)
    # Se crea la carpeta de logs si todavía no existe.
    RUTA_LOGS.mkdir(parents=True, exist_ok=True)
    # Formato de cada línea: fecha | nivel | módulo | mensaje.
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)-10s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    # Manejador que escribe en el archivo (codificación UTF-8 para tildes).
    manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
    # Se aplica el formato al manejador.
    manejador.setFormatter(formato)
    # Se agrega el manejador al logger.
    logger.addHandler(manejador)
    # Se evita que los mensajes suban al logger raíz (no duplicar en consola).
    logger.propagate = False
    return logger


# Logger compartido que importan los demás módulos del sistema.
logger = configurar_logger()

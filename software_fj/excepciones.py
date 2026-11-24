"""
Excepciones personalizadas del sistema Software FJ.

Se define una jerarquía propia para poder distinguir los errores del
dominio (datos inválidos, servicios no disponibles, etc.) de los errores
imprevistos de Python (TypeError, ZeroDivisionError, etc.).
"""


class ErrorSoftwareFJ(Exception):
    """Excepción base de la que heredan todos los errores del sistema."""

    # Código único del tipo de error; cada subclase define el suyo.
    CODIGO = "SFJ-000"

    def __init__(self, mensaje: str):
        # Se pasa el mensaje a Exception para que str(error) funcione.
        super().__init__(mensaje)
        # Se guarda el mensaje como atributo para poder consultarlo.
        self.mensaje = mensaje

    def __str__(self) -> str:
        # Representación estándar: [CÓDIGO] mensaje descriptivo.
        return f"[{self.CODIGO}] {self.mensaje}"


class ErrorValidacion(ErrorSoftwareFJ):
    """Error genérico de validación de datos de entrada."""

    CODIGO = "SFJ-100"


class ClienteInvalidoError(ErrorValidacion):
    """Se lanza cuando los datos de un cliente no cumplen las reglas."""

    CODIGO = "SFJ-101"


class ServicioInvalidoError(ErrorValidacion):
    """Se lanza cuando los datos o parámetros de un servicio son inválidos."""

    CODIGO = "SFJ-102"


class ReservaInvalidaError(ErrorSoftwareFJ):
    """Se lanza cuando una reserva no puede crearse, confirmarse o procesarse."""

    CODIGO = "SFJ-201"


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """Se lanza cuando el servicio (o sus recursos) no está disponible."""

    CODIGO = "SFJ-202"


class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """Se lanza cuando se intenta una operación no válida en el estado actual."""

    CODIGO = "SFJ-203"


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """Se lanza cuando un cálculo de costos produce datos inconsistentes."""

    CODIGO = "SFJ-301"

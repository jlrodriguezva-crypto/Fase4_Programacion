"""
Clase Reserva: integra cliente, servicio, duración y estado.

Implementa confirmación, cancelación y procesamiento con manejo avanzado
de excepciones (try/except/else/finally y encadenamiento con "raise ... from").
"""

from enum import Enum  # enumeración para los estados de la reserva

from .cliente import Cliente
from .entidad import EntidadBase
from .excepciones import (
    ErrorSoftwareFJ,
    ErrorValidacion,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
)
from .formato import pesos
from .registro import logger
from .servicios import Servicio


class EstadoReserva(Enum):
    """Ciclo de vida de una reserva."""

    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    PROCESADA = "Procesada"


class Reserva(EntidadBase):
    """Reserva de un servicio por parte de un cliente."""

    # Prefijo del identificador de las reservas (RES-0001, ...).
    PREFIJO = "RES"

    def __init__(self, cliente, servicio, horas, **opciones):
        # El cliente debe ser una instancia real de Cliente.
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        # El servicio debe ser una instancia de alguna subclase de Servicio.
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        try:
            # El propio servicio valida horas y opciones (cada tipo con sus reglas).
            servicio.validar_parametros(horas, **opciones)
        except ErrorValidacion as error:
            # Se encadena la causa original dentro de un error propio de la reserva.
            raise ReservaInvalidaError(f"No se pudo crear la reserva: {error.mensaje}") from error
        # Atributos privados de la reserva.
        self._cliente = cliente
        self._servicio = servicio
        self._horas = horas
        self._opciones = dict(opciones)  # copia para proteger los datos originales
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = None  # se define al procesar la reserva
        # El identificador se genera al final: una reserva inválida no consume número.
        super().__init__()

    # ------------------------- consultas (solo lectura) -------------------------
    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def horas(self):
        return self._horas

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    # ------------------------- operaciones -------------------------
    def confirmar(self) -> None:
        """Pasa la reserva de PENDIENTE a CONFIRMADA, bloqueando los recursos del servicio."""
        # Solo se puede confirmar una reserva pendiente.
        if self._estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar {self.id}: su estado actual es '{self._estado.value}'."
            )
        try:
            # El servicio verifica disponibilidad y descuenta recursos (p. ej., stock).
            self._servicio.reservar_recursos(**self._opciones)
        except ServicioNoDisponibleError as error:
            # Se encadena el error de disponibilidad en un error de reserva.
            raise ReservaInvalidaError(f"No se pudo confirmar {self.id}: {error.mensaje}") from error
        else:
            # Solo si no hubo error: se actualiza el estado y se registra el evento.
            self._estado = EstadoReserva.CONFIRMADA
            logger.info("Reserva %s confirmada (cliente %s, servicio %s)", self.id, self._cliente.id, self._servicio.id)
        finally:
            # Se ejecuta siempre, haya o no error.
            logger.debug("Intento de confirmación de %s finalizado", self.id)

    def cancelar(self) -> None:
        """Cancela una reserva pendiente o confirmada, liberando recursos si estaban bloqueados."""
        # No se puede cancelar una reserva ya cancelada o procesada.
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar {self.id}: su estado actual es '{self._estado.value}'."
            )
        # Se recuerda si había recursos bloqueados (solo las confirmadas los tienen).
        tenia_recursos = self._estado is EstadoReserva.CONFIRMADA
        try:
            if tenia_recursos:
                # Se devuelven los recursos al servicio (p. ej., unidades al inventario).
                self._servicio.liberar_recursos(**self._opciones)
        finally:
            # Aunque falle la liberación, la reserva queda cancelada y se deja constancia.
            self._estado = EstadoReserva.CANCELADA
            logger.info("Reserva %s cancelada", self.id)

    def procesar(self, descuento=0.0, impuesto=None) -> float:
        """Calcula el costo final de una reserva CONFIRMADA y la marca como PROCESADA."""
        # Solo se procesan reservas confirmadas.
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"No se puede procesar {self.id}: debe estar 'Confirmada' y está '{self._estado.value}'."
            )
        try:
            # Llamada al método sobrecargado de costos del servicio (polimorfismo).
            costo = self._servicio.calcular_costo(self._horas, descuento, impuesto, **self._opciones)
        except ErrorSoftwareFJ as error:
            # Se encadena el error de cálculo en un error propio de la reserva.
            raise ReservaInvalidaError(f"No se pudo procesar {self.id}: {error.mensaje}") from error
        else:
            # Solo si el cálculo fue correcto se cambia el estado y se guarda el costo.
            self._costo_total = costo
            self._estado = EstadoReserva.PROCESADA
            logger.info("Reserva %s procesada. Costo total: %s", self.id, pesos(costo))
            return costo
        finally:
            # Se ejecuta siempre, haya o no error.
            logger.debug("Intento de procesamiento de %s finalizado", self.id)

    def describir(self) -> str:
        # Costo mostrado solo cuando ya fue calculado.
        costo = f" | Costo: {pesos(self._costo_total)}" if self._costo_total is not None else ""
        return (f"Reserva {self.id}: {self._cliente.nombre} -> {self._servicio.nombre} | "
                f"{self._horas} h | Estado: {self._estado.value}{costo}")

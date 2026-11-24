"""Paquete del sistema integral de gestión de clientes, servicios y reservas de Software FJ."""

from .cliente import Cliente
from .excepciones import (
    CalculoInconsistenteError,
    ClienteInvalidoError,
    ErrorSoftwareFJ,
    ErrorValidacion,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
)
from .gestor import GestorSoftwareFJ, Resultado
from .reserva import EstadoReserva, Reserva
from .servicios import AlquilerEquipo, AsesoriaEspecializada, SalaReserva, Servicio

__all__ = [
    "Cliente", "Servicio", "SalaReserva", "AlquilerEquipo", "AsesoriaEspecializada",
    "Reserva", "EstadoReserva", "GestorSoftwareFJ", "Resultado",
    "ErrorSoftwareFJ", "ErrorValidacion", "ClienteInvalidoError", "ServicioInvalidoError",
    "ReservaInvalidaError", "ServicioNoDisponibleError", "OperacionNoPermitidaError",
    "CalculoInconsistenteError",
]

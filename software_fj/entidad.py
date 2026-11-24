"""
Clase abstracta que representa las entidades generales del sistema.

Cliente, Servicio y Reserva heredan de EntidadBase, de modo que todas
comparten un identificador único y la obligación de implementar describir().
"""

from abc import ABC, abstractmethod  # herramientas para clases abstractas


class EntidadBase(ABC):
    """Entidad abstracta: no puede instanciarse directamente."""

    # Prefijo del identificador; cada subclase define el suyo (CLI, SER, RES).
    PREFIJO = "ENT"
    # Contadores por prefijo, compartidos por todas las entidades.
    _contadores: dict = {}

    def __init__(self):
        # Siguiente número consecutivo para este tipo de entidad.
        siguiente = EntidadBase._contadores.get(self.PREFIJO, 0) + 1
        # Se actualiza el contador del prefijo correspondiente.
        EntidadBase._contadores[self.PREFIJO] = siguiente
        # Identificador único, por ejemplo "CLI-0001".
        self._id = f"{self.PREFIJO}-{siguiente:04d}"

    @property
    def id(self) -> str:
        """Identificador de solo lectura (encapsulación)."""
        return self._id

    @abstractmethod
    def describir(self) -> str:
        """Devuelve una descripción legible; cada subclase debe implementarla."""

    def __str__(self) -> str:
        # Al imprimir una entidad se muestra su descripción.
        return self.describir()

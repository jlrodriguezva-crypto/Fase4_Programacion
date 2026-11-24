"""
GestorSoftwareFJ: administra clientes, servicios y reservas en listas internas
(sin base de datos) y garantiza que la aplicación NUNCA se detenga por un error.

Cada operación pública se ejecuta mediante ejecutar_seguro(), que captura las
excepciones, las registra en el archivo de logs y devuelve un Resultado.
"""

import inspect  # permite detectar clases abstractas
from dataclasses import dataclass  # estructura simple para el resultado de cada operación
from typing import Any, Callable, Optional

from .cliente import Cliente
from .excepciones import (
    ErrorSoftwareFJ,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    ServicioInvalidoError,
)
from .registro import logger
from .reserva import EstadoReserva, Reserva
from .servicios import Servicio


@dataclass
class Resultado:
    """Resultado de una operación: éxito o error, sin lanzar excepciones al exterior."""

    exitoso: bool  # True si la operación terminó bien
    valor: Any = None  # objeto resultante (Cliente, Servicio, Reserva, costo...)
    mensaje: str = ""  # mensaje para mostrar al usuario
    error: Optional[Exception] = None  # excepción capturada, si la hubo


class GestorSoftwareFJ:
    """Controlador central del sistema."""

    def __init__(self):
        # Listas internas encapsuladas: reemplazan a la base de datos.
        self._clientes: list = []
        self._servicios: list = []
        self._reservas: list = []

    # ------------------------- ejecución segura -------------------------
    def ejecutar_seguro(self, descripcion: str, funcion: Callable, *args, **kwargs) -> Resultado:
        """Ejecuta una función capturando cualquier error para que el sistema siga activo."""
        try:
            # Se intenta ejecutar la operación solicitada.
            valor = funcion(*args, **kwargs)
        except ErrorSoftwareFJ as error:
            # Errores controlados del dominio: se registra el error y su causa encadenada.
            causa = f" | causa: {error.__cause__!r}" if error.__cause__ else ""
            logger.error("%s FALLÓ: %s%s", descripcion, error, causa)
            return Resultado(False, mensaje=str(error), error=error)
        except Exception as error:  # noqa: BLE001 - se captura todo a propósito
            # Errores imprevistos (TypeError, etc.): se registran con traza completa.
            logger.critical("Error inesperado en '%s': %r", descripcion, error, exc_info=True)
            return Resultado(False, mensaje=f"Error inesperado ({type(error).__name__}): {error}", error=error)
        else:
            # Si no hubo ninguna excepción, la operación se considera exitosa.
            logger.info("%s completada correctamente", descripcion)
            return Resultado(True, valor=valor, mensaje="OK")
        finally:
            # Se ejecuta siempre: deja constancia del fin de cada operación.
            logger.debug("Fin de la operación: %s", descripcion)

    # ------------------------- búsquedas internas -------------------------
    @staticmethod
    def _buscar(lista: list, identificador, tipo: str):
        # Se valida que se haya enviado un identificador (parámetro obligatorio).
        if identificador is None:
            raise ReservaInvalidaError(f"Falta el identificador de {tipo}.")
        # Se recorre la lista buscando el identificador pedido.
        for elemento in lista:
            if elemento.id == identificador:
                return elemento
        # Si no se encontró, se lanza un error controlado.
        raise OperacionNoPermitidaError(f"No existe {tipo} con identificador '{identificador}'.")

    # ------------------------- clientes -------------------------
    def registrar_cliente(self, nombre=None, documento=None, correo=None, telefono=None) -> Resultado:
        """Registra un cliente nuevo validando sus datos y evitando documentos duplicados."""

        def _operacion():
            # Se crea el cliente; si algún dato es inválido, el constructor lanza ClienteInvalidoError.
            cliente = Cliente(nombre, documento, correo, telefono)
            # No se permiten dos clientes con el mismo documento.
            if any(c.documento == cliente.documento for c in self._clientes):
                raise OperacionNoPermitidaError(f"Ya existe un cliente con el documento {cliente.documento}.")
            # Se agrega a la lista interna.
            self._clientes.append(cliente)
            return cliente

        return self.ejecutar_seguro(f"Registro de cliente '{nombre}'", _operacion)

    # ------------------------- servicios -------------------------
    def crear_servicio(self, clase, *args, **kwargs) -> Resultado:
        """Crea un servicio de la clase indicada (SalaReserva, AlquilerEquipo, AsesoriaEspecializada)."""

        def _operacion():
            # Solo se aceptan subclases concretas de Servicio (la clase abstracta no se puede instanciar).
            if not (isinstance(clase, type) and issubclass(clase, Servicio)) or inspect.isabstract(clase):
                raise ServicioInvalidoError(
                    f"'{getattr(clase, '__name__', clase)}' no es un servicio concreto que pueda instanciarse."
                )
            # Se instancia la clase; los constructores validan sus propios datos.
            servicio = clase(*args, **kwargs)
            # Se comprueba que realmente sea un Servicio.
            if not isinstance(servicio, Servicio):
                raise OperacionNoPermitidaError("El objeto creado no es un servicio válido.")
            # Se agrega a la lista interna.
            self._servicios.append(servicio)
            return servicio

        nombre_clase = getattr(clase, "__name__", str(clase))
        return self.ejecutar_seguro(f"Creación de servicio {nombre_clase}", _operacion)

    def cambiar_disponibilidad(self, servicio_id=None, disponible=True) -> Resultado:
        """Marca un servicio como disponible o no disponible."""

        def _operacion():
            servicio = self._buscar(self._servicios, servicio_id, "el servicio")
            servicio.disponible = disponible
            return servicio

        return self.ejecutar_seguro(f"Cambio de disponibilidad de {servicio_id} a {disponible}", _operacion)

    # ------------------------- reservas -------------------------
    def crear_reserva(self, cliente_id=None, servicio_id=None, horas=None, **opciones) -> Resultado:
        """Crea una reserva PENDIENTE para un cliente y un servicio existentes."""

        def _operacion():
            # Se verifica que no falten parámetros obligatorios.
            if cliente_id is None or servicio_id is None or horas is None:
                raise ReservaInvalidaError("Parámetros faltantes: se requieren cliente_id, servicio_id y horas.")
            # Se buscan las entidades en las listas internas.
            cliente = self._buscar(self._clientes, cliente_id, "el cliente")
            servicio = self._buscar(self._servicios, servicio_id, "el servicio")
            # Se crea la reserva (valida horas y opciones del servicio).
            reserva = Reserva(cliente, servicio, horas, **opciones)
            # Se agrega a la lista interna.
            self._reservas.append(reserva)
            return reserva

        return self.ejecutar_seguro(f"Creación de reserva ({cliente_id}, {servicio_id}, {horas} h)", _operacion)

    def confirmar_reserva(self, reserva_id=None) -> Resultado:
        """Confirma una reserva pendiente."""

        def _operacion():
            reserva = self._buscar(self._reservas, reserva_id, "la reserva")
            reserva.confirmar()
            return reserva

        return self.ejecutar_seguro(f"Confirmación de reserva {reserva_id}", _operacion)

    def cancelar_reserva(self, reserva_id=None) -> Resultado:
        """Cancela una reserva pendiente o confirmada."""

        def _operacion():
            reserva = self._buscar(self._reservas, reserva_id, "la reserva")
            reserva.cancelar()
            return reserva

        return self.ejecutar_seguro(f"Cancelación de reserva {reserva_id}", _operacion)

    def procesar_reserva(self, reserva_id=None, descuento=0.0, impuesto=None) -> Resultado:
        """Procesa una reserva confirmada y devuelve su costo total."""

        def _operacion():
            reserva = self._buscar(self._reservas, reserva_id, "la reserva")
            return reserva.procesar(descuento, impuesto)

        return self.ejecutar_seguro(f"Procesamiento de reserva {reserva_id}", _operacion)

    # ------------------------- consultas -------------------------
    def obtener_clientes(self) -> list:
        """Copia de la lista de clientes (protege la lista interna)."""
        return list(self._clientes)

    def obtener_servicios(self) -> list:
        """Copia de la lista de servicios."""
        return list(self._servicios)

    def obtener_reservas(self) -> list:
        """Copia de la lista de reservas."""
        return list(self._reservas)

    def resumen(self) -> dict:
        """Totales del sistema, incluyendo reservas por estado."""
        # Conteo de reservas en cada estado posible.
        por_estado = {e.value: 0 for e in EstadoReserva}
        for reserva in self._reservas:
            por_estado[reserva.estado.value] += 1
        return {
            "clientes": len(self._clientes),
            "servicios": len(self._servicios),
            "reservas": len(self._reservas),
            "reservas_por_estado": por_estado,
        }

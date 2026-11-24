"""
Jerarquía de servicios de Software FJ.

Servicio es una clase abstracta. De ella heredan tres servicios
especializados (SalaReserva, AlquilerEquipo y AsesoriaEspecializada), cada
uno con su propia forma de calcular costos, describirse y validar parámetros
(polimorfismo mediante métodos sobrescritos).

Sobrecarga de métodos: Python no permite dos métodos con el mismo nombre y
distinta firma, por lo que calcular_costo() se sobrecarga de forma simulada
con parámetros opcionales:
    calcular_costo(horas)                          -> costo base + IVA
    calcular_costo(horas, descuento)               -> con descuento
    calcular_costo(horas, descuento, impuesto)     -> con descuento e impuesto propio
    calcular_costo(horas, impuesto=0)              -> solo con impuesto propio
"""

from abc import ABC, abstractmethod  # clases y métodos abstractos

from .entidad import EntidadBase
from .excepciones import (
    CalculoInconsistenteError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
)
from .formato import pesos
from .registro import logger


def _es_numero(valor) -> bool:
    """Indica si el valor es int o float (excluye bool, que es subclase de int)."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


class Servicio(EntidadBase, ABC):
    """Servicio abstracto ofrecido por Software FJ."""

    # Prefijo del identificador de los servicios (SER-0001, ...).
    PREFIJO = "SER"
    # Tasa de IVA por defecto (19 %).
    IVA = 0.19
    # Duración mínima y máxima permitida para una reserva (en horas).
    HORAS_MIN = 1
    HORAS_MAX = 12

    def __init__(self, nombre, tarifa_hora, disponible=True):
        # Cada asignación pasa por su setter, que valida el dato.
        self.nombre = nombre
        self.tarifa_hora = tarifa_hora
        self.disponible = disponible
        # El identificador se genera al final para no consumir números en errores.
        super().__init__()

    # ------------------------- atributos encapsulados -------------------------
    @property
    def nombre(self) -> str:
        """Nombre comercial del servicio."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        # El nombre debe ser texto de al menos 3 caracteres.
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ServicioInvalidoError("El nombre del servicio debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def tarifa_hora(self) -> float:
        """Tarifa por hora en pesos colombianos."""
        return self._tarifa_hora

    @tarifa_hora.setter
    def tarifa_hora(self, valor):
        # La tarifa debe ser un número estrictamente positivo.
        if not _es_numero(valor) or valor <= 0:
            raise ServicioInvalidoError(f"La tarifa por hora debe ser un número positivo (recibido: {valor!r}).")
        self._tarifa_hora = float(valor)

    @property
    def disponible(self) -> bool:
        """Indica si el servicio puede reservarse en este momento."""
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        # La disponibilidad solo admite verdadero o falso.
        if not isinstance(valor, bool):
            raise ServicioInvalidoError("La disponibilidad debe ser True o False.")
        self._disponible = valor

    # ------------------------- métodos abstractos (polimorfismo) -------------------------
    @abstractmethod
    def calcular_costo_base(self, horas, **opciones) -> float:
        """Costo antes de descuentos e impuestos; cada servicio lo calcula distinto."""

    @abstractmethod
    def validar_parametros(self, horas, **opciones) -> None:
        """Valida horas y opciones propias del servicio; lanza ServicioInvalidoError."""

    @abstractmethod
    def describir(self) -> str:
        """Descripción legible del servicio."""

    # ------------------------- utilidades para las subclases -------------------------
    def _validar_horas(self, horas) -> None:
        # Las horas deben ser un número dentro del rango permitido para el servicio.
        if not _es_numero(horas) or not (self.HORAS_MIN <= horas <= self.HORAS_MAX):
            raise ServicioInvalidoError(
                f"Duración inválida ({horas!r}): debe estar entre {self.HORAS_MIN} y "
                f"{self.HORAS_MAX} horas para '{self._nombre}'."
            )

    @staticmethod
    def _rechazar_opciones_extra(otros: dict) -> None:
        # Cualquier opción no reconocida se considera un parámetro inválido.
        if otros:
            raise ServicioInvalidoError(f"Parámetros no reconocidos: {sorted(otros)}.")

    # ------------------------- gestión de recursos -------------------------
    def reservar_recursos(self, **opciones) -> None:
        """Verifica y bloquea los recursos del servicio al confirmar una reserva."""
        # Si el servicio fue marcado como no disponible, no se puede reservar.
        if not self._disponible:
            raise ServicioNoDisponibleError(f"El servicio '{self._nombre}' no está disponible actualmente.")

    def liberar_recursos(self, **opciones) -> None:
        """Libera los recursos al cancelar; por defecto no hay nada que liberar."""

    # ------------------------- método sobrecargado -------------------------
    def calcular_costo(self, horas, descuento=0.0, impuesto=None, **opciones) -> float:
        """
        Calcula el costo total del servicio (sobrecarga simulada con parámetros opcionales).

        horas     : duración del servicio.
        descuento : fracción entre 0 y 1 (0.10 = 10 %). Por defecto sin descuento.
        impuesto  : fracción entre 0 y 1. Si es None se aplica el IVA por defecto.
        opciones  : parámetros propios de cada servicio (asistentes, cantidad, nivel...).
        """
        # Primero se validan los parámetros propios del servicio (lanza error si hay problema).
        self.validar_parametros(horas, **opciones)
        try:
            # Costo base calculado por la subclase (polimorfismo).
            base = self.calcular_costo_base(horas, **opciones)
            # El descuento debe ser una fracción en [0, 1); si no, el cálculo sería inconsistente.
            if not (0 <= descuento < 1):
                raise CalculoInconsistenteError(f"Descuento fuera de rango: {descuento!r} (use 0 a <1).")
            # Se usa el IVA por defecto cuando no se indica impuesto.
            tasa = self.IVA if impuesto is None else impuesto
            # El impuesto debe ser una fracción en [0, 1].
            if not (0 <= tasa <= 1):
                raise CalculoInconsistenteError(f"Impuesto fuera de rango: {tasa!r} (use 0 a 1).")
            # Fórmula: base - descuento + impuesto sobre el valor ya descontado.
            costo = base * (1 - descuento) * (1 + tasa)
        except (TypeError, ArithmeticError) as error:
            # Errores de tipos o aritmética se encadenan en una excepción propia (raise ... from).
            raise CalculoInconsistenteError("No fue posible calcular el costo del servicio.") from error
        else:
            # Solo si no hubo excepción: se verifica que el resultado sea coherente.
            if costo < 0 or costo != costo:  # costo != costo detecta NaN
                raise CalculoInconsistenteError(f"El cálculo produjo un valor inconsistente: {costo!r}.")
            return round(costo, 2)

    def calcular_costo_sin_impuesto(self, horas, descuento=0.0, **opciones) -> float:
        """Variante del cálculo: costo con descuento pero sin impuesto."""
        return self.calcular_costo(horas, descuento, 0, **opciones)


class SalaReserva(Servicio):
    """Reserva de salas de reuniones, con capacidad máxima y recargo opcional de proyector."""

    # Recargo por hora cuando se solicita proyector.
    RECARGO_PROYECTOR = 10000

    def __init__(self, nombre, tarifa_hora, capacidad, disponible=True):
        # La capacidad debe ser un entero positivo.
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise ServicioInvalidoError(f"La capacidad de la sala debe ser un entero positivo (recibido: {capacidad!r}).")
        self._capacidad = capacidad
        # Se completa la construcción con los datos comunes.
        super().__init__(nombre, tarifa_hora, disponible)

    @property
    def capacidad(self) -> int:
        """Número máximo de asistentes."""
        return self._capacidad

    def validar_parametros(self, horas, asistentes=1, proyector=False, **otros) -> None:
        # Se rechazan opciones desconocidas.
        self._rechazar_opciones_extra(otros)
        # Se valida la duración.
        self._validar_horas(horas)
        # Los asistentes deben ser un entero entre 1 y la capacidad de la sala.
        if not isinstance(asistentes, int) or isinstance(asistentes, bool) or not (1 <= asistentes <= self._capacidad):
            raise ServicioInvalidoError(
                f"Asistentes inválidos ({asistentes!r}): la sala '{self._nombre}' admite de 1 a {self._capacidad}."
            )
        # El proyector es una opción verdadero/falso.
        if not isinstance(proyector, bool):
            raise ServicioInvalidoError("La opción 'proyector' debe ser True o False.")

    def calcular_costo_base(self, horas, asistentes=1, proyector=False, **otros) -> float:
        # Costo de la sala por las horas reservadas.
        costo = self._tarifa_hora * horas
        # Si se pide proyector, se suma el recargo por cada hora.
        if proyector:
            costo += self.RECARGO_PROYECTOR * horas
        return costo

    def describir(self) -> str:
        return (f"Sala {self.id}: {self._nombre} | Capacidad: {self._capacidad} personas | "
                f"Tarifa: {pesos(self._tarifa_hora)}/h | Disponible: {'Sí' if self._disponible else 'No'}")


class AlquilerEquipo(Servicio):
    """Alquiler de equipos tecnológicos con inventario (stock) y seguro opcional."""

    # Porcentaje adicional cuando se contrata seguro.
    PORCENTAJE_SEGURO = 0.05

    def __init__(self, nombre, tarifa_hora, stock, disponible=True):
        # El stock debe ser un entero positivo.
        if not isinstance(stock, int) or isinstance(stock, bool) or stock <= 0:
            raise ServicioInvalidoError(f"El stock debe ser un entero positivo (recibido: {stock!r}).")
        self._stock = stock
        # Se completa la construcción con los datos comunes.
        super().__init__(nombre, tarifa_hora, disponible)

    @property
    def stock(self) -> int:
        """Unidades disponibles del equipo."""
        return self._stock

    def validar_parametros(self, horas, cantidad=1, seguro=False, **otros) -> None:
        # Se rechazan opciones desconocidas.
        self._rechazar_opciones_extra(otros)
        # Se valida la duración.
        self._validar_horas(horas)
        # La cantidad solicitada debe ser un entero positivo.
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 1:
            raise ServicioInvalidoError(f"Cantidad inválida ({cantidad!r}): debe ser un entero positivo.")
        # El seguro es una opción verdadero/falso.
        if not isinstance(seguro, bool):
            raise ServicioInvalidoError("La opción 'seguro' debe ser True o False.")

    def calcular_costo_base(self, horas, cantidad=1, seguro=False, **otros) -> float:
        # Costo = tarifa por hora * horas * unidades.
        costo = self._tarifa_hora * horas * cantidad
        # Si se contrata seguro, se agrega un porcentaje.
        if seguro:
            costo *= (1 + self.PORCENTAJE_SEGURO)
        return costo

    def reservar_recursos(self, cantidad=1, **opciones) -> None:
        # Primero se verifica la disponibilidad general (reutiliza la lógica de la clase base).
        super().reservar_recursos(**opciones)
        # Luego se verifica que haya unidades suficientes en inventario.
        if cantidad > self._stock:
            raise ServicioNoDisponibleError(
                f"Stock insuficiente de '{self._nombre}': solicitadas {cantidad}, disponibles {self._stock}."
            )
        # Se descuentan las unidades reservadas del inventario.
        self._stock -= cantidad
        logger.debug("Stock de '%s' actualizado a %d unidades", self._nombre, self._stock)

    def liberar_recursos(self, cantidad=1, **opciones) -> None:
        # Al cancelar, las unidades vuelven al inventario.
        self._stock += cantidad
        logger.debug("Stock de '%s' restaurado a %d unidades", self._nombre, self._stock)

    def describir(self) -> str:
        return (f"Equipo {self.id}: {self._nombre} | Stock: {self._stock} | "
                f"Tarifa: {pesos(self._tarifa_hora)}/h | Disponible: {'Sí' if self._disponible else 'No'}")


class AsesoriaEspecializada(Servicio):
    """Asesoría con especialista; la tarifa depende del nivel del asesor."""

    # Duración máxima de una asesoría (sobrescribe el valor de la clase base).
    HORAS_MAX = 8
    # Multiplicador de tarifa según el nivel del asesor.
    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre, tarifa_hora, especialidad, disponible=True):
        # La especialidad debe ser texto no vacío.
        if not isinstance(especialidad, str) or len(especialidad.strip()) < 3:
            raise ServicioInvalidoError("La especialidad debe tener al menos 3 caracteres.")
        self._especialidad = especialidad.strip()
        # Se completa la construcción con los datos comunes.
        super().__init__(nombre, tarifa_hora, disponible)

    @property
    def especialidad(self) -> str:
        """Área de especialidad de la asesoría."""
        return self._especialidad

    def validar_parametros(self, horas, nivel="junior", **otros) -> None:
        # Se rechazan opciones desconocidas.
        self._rechazar_opciones_extra(otros)
        # Se valida la duración (máximo 8 horas en asesorías).
        self._validar_horas(horas)
        # El nivel debe ser uno de los definidos.
        if nivel not in self.NIVELES:
            raise ServicioInvalidoError(f"Nivel inválido ({nivel!r}): use {', '.join(self.NIVELES)}.")

    def calcular_costo_base(self, horas, nivel="junior", **otros) -> float:
        # Costo = tarifa * horas * multiplicador del nivel del asesor.
        return self._tarifa_hora * horas * self.NIVELES[nivel]

    def describir(self) -> str:
        return (f"Asesoría {self.id}: {self._nombre} | Especialidad: {self._especialidad} | "
                f"Tarifa base: {pesos(self._tarifa_hora)}/h | Disponible: {'Sí' if self._disponible else 'No'}")

"""
Clase Cliente: datos personales encapsulados con validaciones estrictas.
"""

import re  # expresiones regulares para validar formatos

from .entidad import EntidadBase
from .excepciones import ClienteInvalidoError


class Cliente(EntidadBase):
    """Cliente de Software FJ. Sus atributos son privados y se validan al asignarse."""

    # Prefijo del identificador de los clientes (CLI-0001, CLI-0002, ...).
    PREFIJO = "CLI"
    # Nombre: solo letras (con tildes y ñ), espacios y apóstrofes.
    _PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' ]+$")
    # Documento: solo dígitos, entre 6 y 12 caracteres.
    _PATRON_DOCUMENTO = re.compile(r"^\d{6,12}$")
    # Correo: formato básico usuario@dominio.extension.
    _PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
    # Teléfono: solo dígitos, entre 7 y 10 caracteres.
    _PATRON_TELEFONO = re.compile(r"^\d{7,10}$")

    def __init__(self, nombre, documento, correo, telefono):
        # Cada asignación pasa por su setter, que valida y lanza ClienteInvalidoError.
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        # El identificador se genera al final: un cliente inválido no consume número.
        super().__init__()

    # ------------------------- nombre -------------------------
    @property
    def nombre(self) -> str:
        """Nombre completo del cliente."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        # Se exige texto: cualquier otro tipo (o None) es un dato inválido.
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El nombre es obligatorio y debe ser texto.")
        # Se eliminan espacios sobrantes en los extremos.
        valor = valor.strip()
        # Se exige una longitud mínima y solo caracteres permitidos.
        if len(valor) < 3 or not self._PATRON_NOMBRE.match(valor):
            raise ClienteInvalidoError(
                f"Nombre inválido: '{valor}'. Use solo letras (mínimo 3 caracteres)."
            )
        self._nombre = valor

    # ------------------------- documento -------------------------
    @property
    def documento(self) -> str:
        """Número de documento de identidad (solo lectura de facto)."""
        return self._documento

    @documento.setter
    def documento(self, valor):
        # Se acepta número entero o texto, pero se normaliza a texto.
        valor = str(valor).strip() if valor is not None else ""
        # Se valida que sean solo dígitos con la longitud permitida.
        if not self._PATRON_DOCUMENTO.match(valor):
            raise ClienteInvalidoError(
                f"Documento inválido: '{valor}'. Debe tener entre 6 y 12 dígitos."
            )
        self._documento = valor

    # ------------------------- correo -------------------------
    @property
    def correo(self) -> str:
        """Correo electrónico del cliente."""
        return self._correo

    @correo.setter
    def correo(self, valor):
        # Se exige texto para poder validar el formato.
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El correo es obligatorio y debe ser texto.")
        # Se normaliza a minúsculas y sin espacios en los extremos.
        valor = valor.strip().lower()
        # Se valida el formato usuario@dominio.ext.
        if not self._PATRON_CORREO.match(valor):
            raise ClienteInvalidoError(f"Correo inválido: '{valor}'.")
        self._correo = valor

    # ------------------------- teléfono -------------------------
    @property
    def telefono(self) -> str:
        """Teléfono de contacto."""
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        # Se acepta número o texto y se normaliza a texto.
        valor = str(valor).strip() if valor is not None else ""
        # Se valida que sean solo dígitos con la longitud permitida.
        if not self._PATRON_TELEFONO.match(valor):
            raise ClienteInvalidoError(
                f"Teléfono inválido: '{valor}'. Debe tener entre 7 y 10 dígitos."
            )
        self._telefono = valor

    # ------------------------- polimorfismo -------------------------
    def describir(self) -> str:
        # Implementación obligatoria del método abstracto de EntidadBase.
        return (f"Cliente {self.id}: {self._nombre} | Doc: {self._documento} | "
                f"Correo: {self._correo} | Tel: {self._telefono}")

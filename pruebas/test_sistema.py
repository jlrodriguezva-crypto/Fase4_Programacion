"""
Pruebas unitarias del sistema Software FJ.

Ejecución desde la raíz del proyecto:  python -m unittest -v
"""

import logging
import unittest

from software_fj import (
    AlquilerEquipo,
    AsesoriaEspecializada,
    CalculoInconsistenteError,
    Cliente,
    ClienteInvalidoError,
    EstadoReserva,
    GestorSoftwareFJ,
    OperacionNoPermitidaError,
    Reserva,
    ReservaInvalidaError,
    SalaReserva,
    Servicio,
    ServicioInvalidoError,
)
from software_fj.entidad import EntidadBase


def setUpModule():
    # Se desactiva el log durante las pruebas para no contaminar logs/software_fj.log.
    logging.disable(logging.CRITICAL)


def tearDownModule():
    # Se reactiva el log al terminar las pruebas.
    logging.disable(logging.NOTSET)


def crear_cliente():
    """Cliente válido reutilizable en las pruebas."""
    return Cliente("Ana Torres", "1045678901", "ana@correo.com", "3001234567")


class PruebasAbstraccion(unittest.TestCase):
    def test_entidad_y_servicio_son_abstractos(self):
        # Las clases abstractas no pueden instanciarse directamente.
        with self.assertRaises(TypeError):
            EntidadBase()
        with self.assertRaises(TypeError):
            Servicio("Genérico", 1000)


class PruebasCliente(unittest.TestCase):
    def test_cliente_valido(self):
        cliente = crear_cliente()
        self.assertTrue(cliente.id.startswith("CLI-"))
        self.assertEqual(cliente.correo, "ana@correo.com")

    def test_datos_invalidos(self):
        # Cada dato inválido debe lanzar ClienteInvalidoError.
        datos_invalidos = [
            ("A", "1045678901", "a@b.com", "3001234567"),             # nombre muy corto
            ("Ana Torres", "ABC123", "a@b.com", "3001234567"),        # documento con letras
            ("Ana Torres", "1045678901", "sin-arroba", "3001234567"),  # correo inválido
            ("Ana Torres", "1045678901", "a@b.com", "123"),           # teléfono corto
            (None, "1045678901", "a@b.com", "3001234567"),            # nombre faltante
        ]
        for datos in datos_invalidos:
            with self.subTest(datos=datos):
                with self.assertRaises(ClienteInvalidoError):
                    Cliente(*datos)


class PruebasServicios(unittest.TestCase):
    def test_polimorfismo_de_costos(self):
        # Cada servicio calcula su costo base de forma distinta.
        sala = SalaReserva("Sala", 50000, 10)
        equipo = AlquilerEquipo("Portátil", 8000, 5)
        asesoria = AsesoriaEspecializada("Asesoría", 120000, "Arquitectura")
        self.assertEqual(sala.calcular_costo_base(3, asistentes=8, proyector=True), 180000)
        self.assertEqual(equipo.calcular_costo_base(4, cantidad=2), 64000)
        self.assertEqual(asesoria.calcular_costo_base(2, nivel="senior"), 360000)

    def test_sobrecarga_simulada_de_calcular_costo(self):
        sala = SalaReserva("Sala", 50000, 10)
        # Variante 1: solo horas (IVA por defecto 19 %).
        self.assertEqual(sala.calcular_costo(2), 119000.0)
        # Variante 2: horas + descuento.
        self.assertEqual(sala.calcular_costo(2, 0.10), 107100.0)
        # Variante 3: horas + descuento + impuesto propio.
        self.assertEqual(sala.calcular_costo(2, 0.10, 0.05), 94500.0)
        # Variante 4: sin impuesto.
        self.assertEqual(sala.calcular_costo_sin_impuesto(2), 100000.0)

    def test_costos_con_opciones_especificas(self):
        sala = SalaReserva("Sala", 50000, 10)
        equipo = AlquilerEquipo("Portátil", 8000, 5)
        asesoria = AsesoriaEspecializada("Asesoría", 120000, "Arquitectura")
        self.assertEqual(sala.calcular_costo(3, 0.10, asistentes=8, proyector=True), 192780.0)
        self.assertEqual(equipo.calcular_costo(4, cantidad=2, seguro=True), 79968.0)
        self.assertEqual(asesoria.calcular_costo(2, 0.05, nivel="senior"), 406980.0)

    def test_validaciones_de_servicios(self):
        with self.assertRaises(ServicioInvalidoError):
            SalaReserva("Sala", -1, 10)
        with self.assertRaises(ServicioInvalidoError):
            AlquilerEquipo("Portátil", 8000, 0)
        sala = SalaReserva("Sala", 50000, 10)
        with self.assertRaises(ServicioInvalidoError):
            sala.validar_parametros(0)
        with self.assertRaises(ServicioInvalidoError):
            sala.validar_parametros(2, asistentes=11)
        with self.assertRaises(ServicioInvalidoError):
            sala.validar_parametros(2, opcion_inexistente=1)

    def test_calculo_inconsistente(self):
        sala = SalaReserva("Sala", 50000, 10)
        with self.assertRaises(CalculoInconsistenteError):
            sala.calcular_costo(2, descuento=1.5)
        with self.assertRaises(CalculoInconsistenteError):
            sala.calcular_costo(2, impuesto=2)
        # Un tipo incorrecto se convierte en error propio encadenado.
        with self.assertRaises(CalculoInconsistenteError) as contexto:
            sala.calcular_costo(2, descuento="diez")
        self.assertIsInstance(contexto.exception.__cause__, TypeError)


class PruebasReserva(unittest.TestCase):
    def test_ciclo_de_vida_completo(self):
        reserva = Reserva(crear_cliente(), SalaReserva("Sala", 50000, 10), 3, asistentes=8, proyector=True)
        self.assertIs(reserva.estado, EstadoReserva.PENDIENTE)
        reserva.confirmar()
        self.assertIs(reserva.estado, EstadoReserva.CONFIRMADA)
        self.assertEqual(reserva.procesar(descuento=0.10), 192780.0)
        self.assertIs(reserva.estado, EstadoReserva.PROCESADA)

    def test_transiciones_no_permitidas(self):
        reserva = Reserva(crear_cliente(), SalaReserva("Sala", 50000, 10), 2)
        with self.assertRaises(OperacionNoPermitidaError):
            reserva.procesar()  # no se procesa una reserva pendiente
        reserva.cancelar()
        with self.assertRaises(OperacionNoPermitidaError):
            reserva.cancelar()  # no se cancela dos veces
        with self.assertRaises(OperacionNoPermitidaError):
            reserva.confirmar()  # no se confirma una cancelada

    def test_stock_se_descuenta_y_se_restaura(self):
        equipo = AlquilerEquipo("Portátil", 8000, 5)
        reserva = Reserva(crear_cliente(), equipo, 4, cantidad=2)
        reserva.confirmar()
        self.assertEqual(equipo.stock, 3)
        reserva.cancelar()
        self.assertEqual(equipo.stock, 5)

    def test_encadenamiento_de_excepciones(self):
        # Una reserva con horas inválidas conserva la causa original (raise ... from).
        with self.assertRaises(ReservaInvalidaError) as contexto:
            Reserva(crear_cliente(), SalaReserva("Sala", 50000, 10), 0)
        self.assertIsInstance(contexto.exception.__cause__, ServicioInvalidoError)

    def test_servicio_no_disponible(self):
        sala = SalaReserva("Sala", 50000, 10, disponible=False)
        reserva = Reserva(crear_cliente(), sala, 2)
        with self.assertRaises(ReservaInvalidaError):
            reserva.confirmar()
        self.assertIs(reserva.estado, EstadoReserva.PENDIENTE)


class PruebasGestor(unittest.TestCase):
    def test_el_gestor_nunca_lanza_excepciones(self):
        gestor = GestorSoftwareFJ()
        # Operaciones con datos inválidos, faltantes o inexistentes: ninguna debe propagar error.
        resultados = [
            gestor.registrar_cliente("X", "1", "malo", "1"),
            gestor.registrar_cliente(),
            gestor.crear_servicio(Servicio, "Genérico", 1000),
            gestor.crear_servicio(SalaReserva, "Sala", -1, 5),
            gestor.crear_reserva(),
            gestor.crear_reserva("CLI-9999", "SER-9999", 2),
            gestor.confirmar_reserva("RES-9999"),
            gestor.procesar_reserva(None),
            gestor.ejecutar_seguro("Error inesperado", lambda: 1 / 0),
        ]
        for resultado in resultados:
            self.assertFalse(resultado.exitoso)
            self.assertIsNotNone(resultado.error)

    def test_documento_duplicado(self):
        gestor = GestorSoftwareFJ()
        self.assertTrue(gestor.registrar_cliente("Ana Torres", "1045678901", "a@b.com", "3001234567").exitoso)
        duplicado = gestor.registrar_cliente("Otra Persona", "1045678901", "c@d.com", "3007654321")
        self.assertFalse(duplicado.exitoso)
        self.assertIsInstance(duplicado.error, OperacionNoPermitidaError)

    def test_flujo_exitoso_y_resumen(self):
        gestor = GestorSoftwareFJ()
        cliente = gestor.registrar_cliente("Ana Torres", "1045678901", "a@b.com", "3001234567").valor
        sala = gestor.crear_servicio(SalaReserva, "Sala", 50000, 10).valor
        reserva = gestor.crear_reserva(cliente.id, sala.id, 2, asistentes=4).valor
        self.assertTrue(gestor.confirmar_reserva(reserva.id).exitoso)
        self.assertEqual(gestor.procesar_reserva(reserva.id).valor, 119000.0)
        resumen = gestor.resumen()
        self.assertEqual(resumen["reservas_por_estado"]["Procesada"], 1)


if __name__ == "__main__":
    unittest.main()

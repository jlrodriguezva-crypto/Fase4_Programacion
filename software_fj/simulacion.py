"""
Simulación de operaciones completas del sistema Software FJ.

Se ejecutan más de 10 operaciones sin base de datos: registros válidos e
inválidos de clientes, creación correcta e incorrecta de servicios y reservas
exitosas y fallidas. El programa continúa funcionando después de cada error
y todo queda registrado en logs/software_fj.log.
"""

from .formato import pesos
from .gestor import GestorSoftwareFJ, Resultado
from .registro import ARCHIVO_LOG, logger
from .servicios import AlquilerEquipo, AsesoriaEspecializada, SalaReserva, Servicio


class Simulador:
    """Ejecuta y muestra por consola cada operación de la simulación."""

    def __init__(self):
        # Gestor central con las listas internas de clientes, servicios y reservas.
        self.gestor = GestorSoftwareFJ()
        # Contadores de operaciones exitosas y fallidas.
        self.total = 0
        self.exitosas = 0
        self.fallidas = 0

    def mostrar(self, descripcion: str, resultado: Resultado) -> Resultado:
        """Imprime el resultado de una operación y actualiza los contadores."""
        # Se numera cada operación.
        self.total += 1
        if resultado.exitoso:
            self.exitosas += 1
            print(f"[{self.total:02d}] OK     {descripcion}")
        else:
            self.fallidas += 1
            print(f"[{self.total:02d}] ERROR  {descripcion}\n         -> {resultado.mensaje}")
        return resultado

    def ejecutar(self) -> None:
        """Corre la secuencia completa de operaciones."""
        g = self.gestor
        logger.info("===== INICIO DE LA SIMULACIÓN =====")
        print("=" * 78)
        print("SOFTWARE FJ - Simulación del sistema de clientes, servicios y reservas")
        print("=" * 78)

        # ---------------- CLIENTES ----------------
        print("\n--- Registro de clientes ---")
        ana = self.mostrar("Cliente válido: Ana María Torres",
                           g.registrar_cliente("Ana María Torres", "1045678901", "ana.torres@correo.com", "3001234567"))
        carlos = self.mostrar("Cliente válido: Carlos Pérez",
                              g.registrar_cliente("Carlos Pérez", 79123456, "carlos.perez@empresa.co", "3109876543"))
        self.mostrar("Cliente inválido: correo sin '@'",
                     g.registrar_cliente("Luis Gómez", "80123456", "luis.gomez.correo.com", "3201112233"))
        self.mostrar("Cliente inválido: documento con letras",
                     g.registrar_cliente("Marta Ruiz", "ABC123", "marta@correo.com", "3112223344"))
        self.mostrar("Cliente duplicado: mismo documento de Carlos",
                     g.registrar_cliente("Carlos Pérez Duplicado", "79123456", "otro@correo.com", "3005556677"))

        # ---------------- SERVICIOS ----------------
        print("\n--- Creación de servicios ---")
        sala = self.mostrar("Servicio válido: Sala Ejecutiva (10 personas)",
                            g.crear_servicio(SalaReserva, "Sala Ejecutiva", 50000, 10))
        equipo = self.mostrar("Servicio válido: Alquiler Portátil Dell (stock 5)",
                              g.crear_servicio(AlquilerEquipo, "Portátil Dell Latitude", 8000, 5))
        asesoria = self.mostrar("Servicio válido: Asesoría en Arquitectura de Software",
                                g.crear_servicio(AsesoriaEspecializada, "Arquitectura de software", 120000, "Arquitectura"))
        self.mostrar("Servicio inválido: tarifa negativa",
                     g.crear_servicio(SalaReserva, "Sala Económica", -5000, 6))
        self.mostrar("Servicio inválido: clase abstracta Servicio (no instanciable)",
                     g.crear_servicio(Servicio, "Servicio genérico", 10000))

        # Identificadores de los objetos creados (None si alguna creación hubiese fallado).
        id_ana = ana.valor.id if ana.exitoso else None
        id_carlos = carlos.valor.id if carlos.exitoso else None
        id_sala = sala.valor.id if sala.exitoso else None
        id_equipo = equipo.valor.id if equipo.exitoso else None
        id_asesoria = asesoria.valor.id if asesoria.exitoso else None

        # ---------------- RESERVAS ----------------
        print("\n--- Reservas exitosas ---")
        r1 = self.mostrar("Crear reserva de sala: 3 h, 8 asistentes, con proyector",
                          g.crear_reserva(id_ana, id_sala, 3, asistentes=8, proyector=True))
        id_r1 = r1.valor.id if r1.exitoso else None
        self.mostrar("Confirmar reserva de sala", g.confirmar_reserva(id_r1))
        costo = self.mostrar("Procesar reserva de sala con 10 % de descuento",
                             g.procesar_reserva(id_r1, descuento=0.10))
        if costo.exitoso:
            print(f"         -> Costo total (IVA 19 % incluido): {pesos(costo.valor)}")

        r2 = self.mostrar("Crear reserva de equipo: 4 h, 2 unidades, con seguro",
                          g.crear_reserva(id_carlos, id_equipo, 4, cantidad=2, seguro=True))
        id_r2 = r2.valor.id if r2.exitoso else None
        self.mostrar("Confirmar reserva de equipo (stock 5 -> 3)", g.confirmar_reserva(id_r2))
        self.mostrar("Cancelar reserva de equipo (stock vuelve a 5)", g.cancelar_reserva(id_r2))

        # ---------------- RESERVAS FALLIDAS ----------------
        print("\n--- Reservas y operaciones fallidas ---")
        self.mostrar("Reserva con duración inválida (0 horas)",
                     g.crear_reserva(id_ana, id_sala, 0, asistentes=2))
        self.mostrar("Reserva de sala con más asistentes que la capacidad (12 > 10)",
                     g.crear_reserva(id_ana, id_sala, 2, asistentes=12))
        self.mostrar("Reserva con parámetros faltantes (sin servicio ni horas)",
                     g.crear_reserva(id_ana))
        self.mostrar("Reserva para un cliente inexistente",
                     g.crear_reserva("CLI-9999", id_sala, 2))

        r3 = self.mostrar("Crear reserva de 9 unidades de equipo (válida al crear)",
                          g.crear_reserva(id_carlos, id_equipo, 2, cantidad=9))
        id_r3 = r3.valor.id if r3.exitoso else None
        self.mostrar("Confirmar reserva de 9 unidades: stock insuficiente", g.confirmar_reserva(id_r3))
        self.mostrar("Procesar una reserva que sigue pendiente", g.procesar_reserva(id_r3))
        self.mostrar("Cancelar dos veces la misma reserva (segundo intento)", g.cancelar_reserva(id_r2))

        # ---------------- DISPONIBILIDAD Y CÁLCULOS ----------------
        print("\n--- Disponibilidad y cálculos ---")
        self.mostrar("Marcar la asesoría como no disponible", g.cambiar_disponibilidad(id_asesoria, False))
        r4 = self.mostrar("Crear reserva de asesoría senior de 2 h",
                          g.crear_reserva(id_ana, id_asesoria, 2, nivel="senior"))
        id_r4 = r4.valor.id if r4.exitoso else None
        self.mostrar("Confirmar asesoría con el servicio no disponible", g.confirmar_reserva(id_r4))
        self.mostrar("Reactivar la asesoría", g.cambiar_disponibilidad(id_asesoria, True))
        self.mostrar("Confirmar asesoría ahora disponible", g.confirmar_reserva(id_r4))
        self.mostrar("Procesar asesoría con descuento inválido (150 %)",
                     g.procesar_reserva(id_r4, descuento=1.5))
        costo2 = self.mostrar("Procesar asesoría con 5 % de descuento",
                              g.procesar_reserva(id_r4, descuento=0.05))
        if costo2.exitoso:
            print(f"         -> Costo total (IVA 19 % incluido): {pesos(costo2.valor)}")

        # Error imprevisto: llamar al cálculo sin el parámetro obligatorio 'horas'.
        if asesoria.exitoso:
            self.mostrar("Cálculo directo sin el parámetro 'horas' (error inesperado)",
                         g.ejecutar_seguro("Cálculo directo de costo", asesoria.valor.calcular_costo))

        # ---------------- RESUMEN ----------------
        self.imprimir_resumen()
        logger.info("===== FIN DE LA SIMULACIÓN: %d operaciones (%d OK, %d con error) =====",
                    self.total, self.exitosas, self.fallidas)

    def imprimir_resumen(self) -> None:
        """Muestra el estado final del sistema y el resumen de operaciones."""
        g = self.gestor
        print("\n" + "=" * 78)
        print("ESTADO FINAL DEL SISTEMA")
        print("=" * 78)
        for cliente in g.obtener_clientes():
            print(" ", cliente)
        for servicio in g.obtener_servicios():
            print(" ", servicio)
        for reserva in g.obtener_reservas():
            print(" ", reserva)
        datos = g.resumen()
        print(f"\nTotales -> clientes: {datos['clientes']} | servicios: {datos['servicios']} | "
              f"reservas: {datos['reservas']} {datos['reservas_por_estado']}")
        print(f"Operaciones ejecutadas: {self.total} | exitosas: {self.exitosas} | "
              f"con error controlado: {self.fallidas}")
        print("El sistema continuó funcionando después de cada error.")
        print(f"Registro de eventos y errores: {ARCHIVO_LOG}")


def ejecutar_simulacion() -> None:
    """Punto de entrada de la simulación."""
    Simulador().ejecutar()

# Software FJ – Sistema integral de gestión de clientes, servicios y reservas

Proyecto de la **Fase 4 – Prácticas simuladas** del curso **Programación (213023)**, Universidad Nacional Abierta y a Distancia (UNAD).

Sistema orientado a objetos en Python, **sin base de datos**, que gestiona clientes, servicios y reservas de la empresa ficticia *Software FJ*, con manejo avanzado de excepciones y registro de eventos en un archivo de logs.

## Autor

| Autor | Grupo |
|---|---|
| Jose Luis Rodríguez Vásquez | 213023_49 |

## Requisitos

- Python 3.10 o superior.
- Solo se usa la biblioteca estándar (no hay dependencias que instalar).

## Ejecución

```bash
# Simulación completa (32 operaciones válidas e inválidas)
python main.py

# Pruebas unitarias (16 pruebas)
python -m unittest -v
```

Todos los eventos y errores quedan registrados en `logs/software_fj.log`.

## Estructura del proyecto

```
SoftwareFJ/
├── main.py                    # Punto de entrada
├── software_fj/
│   ├── excepciones.py         # Jerarquía de excepciones personalizadas
│   ├── registro.py            # Configuración del archivo de logs
│   ├── entidad.py             # Clase abstracta EntidadBase
│   ├── cliente.py             # Cliente (datos encapsulados y validados)
│   ├── servicios.py           # Servicio (abstracta) + 3 servicios especializados
│   ├── reserva.py             # Reserva: confirmar, cancelar y procesar
│   ├── gestor.py              # GestorSoftwareFJ: listas internas + ejecución segura
│   ├── formato.py             # Formato de valores en pesos
│   └── simulacion.py          # Simulación de operaciones
├── pruebas/test_sistema.py    # Pruebas unitarias
└── logs/software_fj.log       # Registro de eventos y errores
```

## Conceptos de POO aplicados

| Concepto | Dónde se aplica |
|---|---|
| **Abstracción** | `EntidadBase` y `Servicio` son clases abstractas (`ABC`, `@abstractmethod`). |
| **Herencia** | `Cliente`, `Servicio` y `Reserva` heredan de `EntidadBase`; `SalaReserva`, `AlquilerEquipo` y `AsesoriaEspecializada` heredan de `Servicio`. |
| **Polimorfismo** | Cada servicio sobrescribe `calcular_costo_base()`, `validar_parametros()` y `describir()`. |
| **Encapsulación** | Atributos privados (`_nombre`, `_stock`, ...) con propiedades y validación en los *setters*. |
| **Sobrecarga (simulada)** | `calcular_costo(horas, descuento=0.0, impuesto=None, **opciones)` admite varias combinaciones de parámetros, porque Python no permite sobrecarga real. |

## Manejo de excepciones

| Excepción | Código | Cuándo se lanza |
|---|---|---|
| `ClienteInvalidoError` | SFJ-101 | Datos de cliente inválidos |
| `ServicioInvalidoError` | SFJ-102 | Datos o parámetros de servicio inválidos |
| `ReservaInvalidaError` | SFJ-201 | La reserva no puede crearse, confirmarse o procesarse |
| `ServicioNoDisponibleError` | SFJ-202 | Servicio no disponible o stock insuficiente |
| `OperacionNoPermitidaError` | SFJ-203 | Operación no válida para el estado actual (o duplicados/inexistentes) |
| `CalculoInconsistenteError` | SFJ-301 | Descuento o impuesto fuera de rango, o resultado inconsistente |

Técnicas utilizadas:

- `try / except` en las validaciones y el cálculo de costos.
- `try / except / else` en `Servicio.calcular_costo()`, `Reserva.confirmar()` y `Reserva.procesar()`.
- `try / except / finally` en `GestorSoftwareFJ.ejecutar_seguro()`, `Reserva.confirmar()` y `Reserva.procesar()`; `try / finally` en `Reserva.cancelar()`.
- **Encadenamiento** con `raise ... from error`: la causa original se conserva en `__cause__` y se escribe en el log.
- Los errores imprevistos (`TypeError`, etc.) se capturan en `ejecutar_seguro()` y se registran con la traza completa, de modo que la aplicación nunca se detiene.

## Reglas de negocio

- **Sala:** tarifa por hora + recargo de proyector por hora; asistentes entre 1 y la capacidad de la sala.
- **Equipo:** tarifa × horas × unidades (+5 % si se contrata seguro); el stock se descuenta al confirmar y se restaura al cancelar.
- **Asesoría:** tarifa × horas × multiplicador de nivel (junior 1.0, senior 1.5, experto 2.0); máximo 8 horas.
- **Costo final:** `base × (1 − descuento) × (1 + IVA)`, con IVA por defecto del 19 %.
- **Estados de la reserva:** Pendiente → Confirmada → Procesada; se puede cancelar mientras esté Pendiente o Confirmada.

## Simulación

`python main.py` ejecuta 32 operaciones: 17 exitosas y 15 con error controlado (correo inválido, documento duplicado, tarifa negativa, clase abstracta, horas inválidas, capacidad excedida, parámetros faltantes, cliente inexistente, stock insuficiente, servicio no disponible, transiciones de estado no permitidas, descuento fuera de rango y un error inesperado de tipo `TypeError`). El sistema continúa después de cada error y los registra en `logs/software_fj.log`.

## Referencias

- Van Rossum, G., & Drake Jr, F. L. (2024). *El tutorial de Python* (cap. 8, Errores y excepciones). Python Software Foundation. https://docs.python.org/es/3.12/tutorial/errors.html

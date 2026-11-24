"""Utilidades de formato compartidas por todo el sistema."""


def pesos(valor: float) -> str:
    """Formatea un valor como pesos colombianos (punto como separador de miles)."""
    # Se da formato con comas y luego se cambian por puntos: 1,234,567 -> 1.234.567.
    return "$" + f"{valor:,.0f}".replace(",", ".")

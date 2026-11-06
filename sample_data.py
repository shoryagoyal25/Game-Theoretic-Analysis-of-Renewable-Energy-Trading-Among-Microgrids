"""Illustrative sample data; values are simulated, not measured data."""
from microgrid import Microgrid


def default_microgrids() -> list[Microgrid]:
    return [
        Microgrid("A", 80, 50, 10.0, 5.0),
        Microgrid("B", 40, 65, 11.0, 5.5),
        Microgrid("C", 100, 70, 10.5, 5.0),
        Microgrid("D", 30, 55, 12.0, 6.0),
        Microgrid("E", 60, 45, 9.5, 4.5),
    ]

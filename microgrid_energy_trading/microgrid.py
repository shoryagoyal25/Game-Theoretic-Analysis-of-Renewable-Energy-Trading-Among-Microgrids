"""Core microgrid data model and energy-balance calculations."""
from dataclasses import dataclass
from typing import Dict


@dataclass
class Microgrid:
    name: str
    solar_generation: float
    demand: float
    grid_price: float = 10.0
    min_sell_price: float = 5.0
    battery_capacity: float = 0.0  # Reserved for future extension; no storage dispatch modeled.

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Microgrid name cannot be empty.")
        for field_name in ("solar_generation", "demand", "grid_price", "min_sell_price", "battery_capacity"):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative.")
        if self.min_sell_price > self.grid_price:
            # This is allowed as configuration, but it means the grid may have no feasible buyer.
            pass

    @property
    def net_energy(self) -> float:
        return self.solar_generation - self.demand

    @property
    def surplus(self) -> float:
        return max(self.net_energy, 0.0)

    @property
    def deficit(self) -> float:
        return max(-self.net_energy, 0.0)

    def energy_balance(self) -> Dict[str, float | str]:
        return {"Microgrid": self.name, "Solar Generation (kWh)": self.solar_generation,
                "Demand (kWh)": self.demand, "Net Energy (kWh)": self.net_energy,
                "Surplus (kWh)": self.surplus, "Deficit (kWh)": self.deficit}

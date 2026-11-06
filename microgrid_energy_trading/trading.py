"""Direct renewable energy marketplace with feasibility and accounting checks."""
from dataclasses import dataclass
from typing import Iterable
import pandas as pd
from microgrid import Microgrid


@dataclass(frozen=True)
class Transaction:
    seller: str
    buyer: str
    energy_kwh: float
    price_per_kwh: float

    @property
    def total_value(self) -> float:
        return self.energy_kwh * self.price_per_kwh


def negotiated_price(seller: Microgrid, buyer: Microgrid) -> float | None:
    """Midpoint price; feasible only if seller reservation <= buyer avoided grid price."""
    if seller.min_sell_price > buyer.grid_price:
        return None
    return (seller.min_sell_price + buyer.grid_price) / 2.0


def match_energy(microgrids: Iterable[Microgrid], seller_fraction: float | dict[str, float] = 1.0,
                 buyer_fraction: float | dict[str, float] = 1.0) -> list[Transaction]:
    """Greedy deterministic matching, prioritizing buyers with the highest grid price.

    Fractions in [0, 1] represent the finite strategic participation choices used by
    the game model. Sellers are sorted by reservation price; buyers by avoided grid cost.
    """
    grids = list(microgrids)
    def fraction_for(spec, name):
        value = spec.get(name, 1.0) if isinstance(spec, dict) else spec
        if not 0 <= value <= 1:
            raise ValueError("Participation fractions must be between 0 and 1.")
        return value
    sellers = sorted([g for g in grids if g.surplus > 0], key=lambda g: (g.min_sell_price, g.name))
    buyers = sorted([g for g in grids if g.deficit > 0], key=lambda g: (-g.grid_price, g.name))
    remaining_supply = {g.name: g.surplus * fraction_for(seller_fraction, g.name) for g in sellers}
    remaining_demand = {g.name: g.deficit * fraction_for(buyer_fraction, g.name) for g in buyers}
    transactions: list[Transaction] = []
    for buyer in buyers:
        for seller in sellers:
            if buyer.name == seller.name or remaining_demand[buyer.name] <= 1e-9:
                continue
            price = negotiated_price(seller, buyer)
            if price is None or remaining_supply[seller.name] <= 1e-9:
                continue
            qty = min(remaining_supply[seller.name], remaining_demand[buyer.name])
            if qty <= 1e-9:
                continue
            transactions.append(Transaction(seller.name, buyer.name, qty, price))
            remaining_supply[seller.name] -= qty
            remaining_demand[buyer.name] -= qty
    # Accounting invariants
    for seller in sellers:
        sold = sum(t.energy_kwh for t in transactions if t.seller == seller.name)
        assert sold <= seller.surplus * fraction_for(seller_fraction, seller.name) + 1e-7
    for buyer in buyers:
        bought = sum(t.energy_kwh for t in transactions if t.buyer == buyer.name)
        assert bought <= buyer.deficit * fraction_for(buyer_fraction, buyer.name) + 1e-7
    return transactions


def transactions_frame(transactions: list[Transaction]) -> pd.DataFrame:
    columns = ["Seller", "Buyer", "Energy (kWh)", "Price (₹/kWh)", "Transaction Value (₹)"]
    return pd.DataFrame([{"Seller": t.seller, "Buyer": t.buyer, "Energy (kWh)": t.energy_kwh,
                          "Price (₹/kWh)": t.price_per_kwh, "Transaction Value (₹)": t.total_value}
                         for t in transactions], columns=columns)

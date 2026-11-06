import pytest
from microgrid import Microgrid
from trading import match_energy, transactions_frame

def test_trades_respect_supply_demand_and_feasible_price():
    grids = [Microgrid("S", 30, 10, 10, 4), Microgrid("B", 5, 25, 12, 5), Microgrid("X", 5, 5, 10, 4)]
    tx = match_energy(grids)
    assert sum(t.energy_kwh for t in tx if t.seller == "S") <= 20 + 1e-9
    assert sum(t.energy_kwh for t in tx if t.buyer == "B") <= 20 + 1e-9
    assert all(t.price_per_kwh >= 4 and t.price_per_kwh <= 12 for t in tx)
    assert all(t.energy_kwh >= 0 and t.total_value >= 0 for t in tx)

def test_no_trade_when_price_infeasible():
    grids = [Microgrid("S", 20, 0, 5, 15), Microgrid("B", 0, 20, 10, 2)]
    assert match_energy(grids) == []

def test_invalid_fraction():
    with pytest.raises(ValueError):
        match_energy([Microgrid("S", 10, 0), Microgrid("B", 0, 10)], seller_fraction=1.2)

def test_transaction_frame_columns():
    df = transactions_frame([])
    assert "Transaction Value (₹)" in df.columns

from microgrid import Microgrid
from trading import match_energy
from analysis import analyze_results

def test_accounting_and_community_savings():
    grids = [Microgrid("S", 30, 10, 10, 4), Microgrid("B", 5, 25, 12, 5), Microgrid("X", 5, 5, 10, 4)]
    tx = match_energy(grids)
    individual, community = analyze_results(grids, tx)
    assert abs(individual["Sales Revenue (₹)"].sum() - individual["Purchase Payments (₹)"].sum()) < 1e-6
    metrics = dict(zip(community.Metric, community.Value))
    assert metrics["Community operating-cost savings (₹)"] >= 0
    assert metrics["Total energy traded (kWh)"] == sum(t.energy_kwh for t in tx)

def test_repeatable_results():
    grids = [Microgrid("S", 30, 10, 10, 4), Microgrid("B", 5, 25, 12, 5)]
    assert match_energy(grids) == match_energy(grids)

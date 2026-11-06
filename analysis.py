"""Financial and community performance calculations."""
import pandas as pd
from microgrid import Microgrid
from trading import Transaction


def analyze_results(microgrids: list[Microgrid], transactions: list[Transaction]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for g in microgrids:
        sold = sum(t.energy_kwh for t in transactions if t.seller == g.name)
        bought = sum(t.energy_kwh for t in transactions if t.buyer == g.name)
        revenue = sum(t.total_value for t in transactions if t.seller == g.name)
        payment = sum(t.total_value for t in transactions if t.buyer == g.name)
        external_before = g.deficit
        external_after = max(g.deficit - bought, 0.0)
        cost_before = external_before * g.grid_price
        cost_after = external_after * g.grid_price + payment - revenue
        # Net benefit vs no-trade baseline includes sales revenue or purchase payments.
        savings = cost_before - cost_after
        rows.append({"Microgrid": g.name, "Initial Surplus (kWh)": g.surplus, "Initial Deficit (kWh)": g.deficit,
                     "Energy Sold (kWh)": sold, "Energy Purchased (kWh)": bought,
                     "Sales Revenue (₹)": revenue, "Purchase Payments (₹)": payment,
                     "External Grid Purchase Before (kWh)": external_before,
                     "External Grid Purchase After (kWh)": external_after,
                     "Electricity Cost Before (₹)": cost_before, "Net Cost After Trading (₹)": cost_after,
                     "Net Individual Savings (₹)": savings})
    individual = pd.DataFrame(rows)
    total_generation = sum(g.solar_generation for g in microgrids)
    total_demand = sum(g.demand for g in microgrids)
    total_traded = sum(t.energy_kwh for t in transactions)
    external_before = sum(g.deficit for g in microgrids)
    external_after = sum(max(g.deficit - sum(t.energy_kwh for t in transactions if t.buyer == g.name), 0.0) for g in microgrids)
    cost_before = sum(g.deficit * g.grid_price for g in microgrids)
    # Community cost excludes internal transfers; they cancel between participants.
    cost_after = sum(max(g.deficit - sum(t.energy_kwh for t in transactions if t.buyer == g.name), 0.0) * g.grid_price
                     for g in microgrids)
    metrics = pd.DataFrame([
        {"Metric": "Total solar generation (kWh)", "Value": total_generation},
        {"Metric": "Total electricity demand (kWh)", "Value": total_demand},
        {"Metric": "Total energy traded (kWh)", "Value": total_traded},
        {"Metric": "External-grid purchases before trading (kWh)", "Value": external_before},
        {"Metric": "External-grid purchases after trading (kWh)", "Value": external_after},
        {"Metric": "Community cost before trading (₹)", "Value": cost_before},
        {"Metric": "Community cost after trading (₹)", "Value": cost_after},
        {"Metric": "Community operating-cost savings (₹)", "Value": cost_before - cost_after},
        {"Metric": "Renewable utilization rate (%)", "Value": (min(total_generation, total_demand) / total_generation * 100 if total_generation else 0.0)},
    ])
    # Internal payments must balance exactly, up to floating point precision.
    assert abs(sum(individual["Sales Revenue (₹)"]) - sum(individual["Purchase Payments (₹)"])) < 1e-6
    return individual, metrics

"""Interactive Plotly charts and NetworkX trading-network layout."""
import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from microgrid import Microgrid
from trading import Transaction


def generation_demand_chart(grids: list[Microgrid]):
    df = pd.DataFrame([{"Microgrid": g.name, "Solar Generation": g.solar_generation, "Demand": g.demand} for g in grids])
    return px.bar(df, x="Microgrid", y=["Solar Generation", "Demand"], barmode="group", title="Solar Generation vs Demand (kWh)")


def balance_chart(grids: list[Microgrid]):
    df = pd.DataFrame([{"Microgrid": g.name, "Surplus": g.surplus, "Deficit": -g.deficit} for g in grids])
    return px.bar(df, x="Microgrid", y=["Surplus", "Deficit"], barmode="relative", title="Initial Surplus (+) and Deficit (−), kWh")


def network_chart(grids: list[Microgrid], transactions: list[Transaction]):
    graph = nx.DiGraph()
    for g in grids:
        graph.add_node(g.name, role="seller" if g.surplus else "buyer" if g.deficit else "balanced")
    for t in transactions:
        graph.add_edge(t.seller, t.buyer, energy=t.energy_kwh, price=t.price_per_kwh)
    pos = nx.spring_layout(graph, seed=17)
    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1.5), hoverinfo="none", name="Trades"))
    fig.add_trace(go.Scatter(x=[pos[n][0] for n in graph.nodes()], y=[pos[n][1] for n in graph.nodes()],
        mode="markers+text", text=list(graph.nodes()), textposition="top center", marker=dict(size=28),
        hovertext=[f"{n}: {graph.nodes[n]['role']}" for n in graph.nodes()], hoverinfo="text", name="Microgrids"))
    fig.update_layout(title="Energy Trading Network", showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def cost_chart(individual: pd.DataFrame):
    return px.bar(individual, x="Microgrid", y=["Electricity Cost Before (₹)", "Net Cost After Trading (₹)"],
                  barmode="group", title="Individual Electricity Cost Before vs After Trading")


def savings_chart(individual: pd.DataFrame):
    return px.bar(individual, x="Microgrid", y="Net Individual Savings (₹)", title="Net Individual Benefit (₹)")


def payoff_chart(strategy_table: pd.DataFrame, grids: list[Microgrid]):
    if strategy_table.empty:
        return go.Figure().update_layout(title="No strategy profiles")
    payoff_cols = [g.name + " Payoff (₹)" for g in grids]
    means = strategy_table[payoff_cols].mean().reset_index()
    means.columns = ["Microgrid", "Mean payoff (₹)"]
    return px.bar(means, x="Microgrid", y="Mean payoff (₹)", title="Average Payoff Across Enumerated Profiles (₹)")

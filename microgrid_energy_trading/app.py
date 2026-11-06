"""Streamlit dashboard for game-theoretic renewable energy trading."""
import pandas as pd
import streamlit as st
from microgrid import Microgrid
from sample_data import default_microgrids
from trading import match_energy, transactions_frame
from analysis import analyze_results
from game_theory import STRATEGIES, find_pure_nash_equilibria, best_responses, profile_payoffs
from visualization import generation_demand_chart, balance_chart, network_chart, cost_chart, savings_chart, payoff_chart

st.set_page_config(page_title="Microgrid Energy Trading Lab", page_icon="🌱", layout="wide")
st.markdown("""<style>
.stApp {background: #f5f8f6;} [data-testid="stMetric"] {background:#ffffff;padding:14px;border-radius:12px;border-left:4px solid #2d8a61;}
h1,h2,h3 {color:#12334a;} .stButton>button {background:#176b4d;color:white;border-radius:8px;}
</style>""", unsafe_allow_html=True)

st.title("🌱 Game-Theoretic Analysis of Renewable Energy Trading Among Microgrids")
st.caption("Interactive simulation • illustrative data only • ₹ and kWh • no paid APIs")

with st.sidebar:
    st.header("Simulation controls")
    if "grid_data" not in st.session_state:
        st.session_state.grid_data = pd.DataFrame([g.__dict__ for g in default_microgrids()])
    if st.button("Reset to sample data"):
        st.session_state.grid_data = pd.DataFrame([g.__dict__ for g in default_microgrids()])
    st.markdown("**Participation strategy** is evaluated separately in the Game Theory tab.")
    st.info("Data are simulated examples, not real-world measurements. Batteries are configurable but storage dispatch is not modeled.")

pages = st.tabs(["Overview", "Configure & Energy", "Marketplace", "Game Theory Lab", "Results & Export", "Mathematical Model"])
with pages[0]:
    st.subheader("Project overview")
    st.write("**Abstract.** This project simulates direct renewable electricity exchange among connected microgrids. It calculates local surpluses and deficits, matches feasible sellers and buyers, estimates individual and community costs, and separately evaluates a finite non-cooperative participation game.")
    st.write("**Problem statement.** Solar output and electricity demand vary across microgrids. Without coordination, a surplus microgrid may leave energy unused while a neighboring deficit microgrid purchases electricity from the external grid.")
    st.write("**Objectives**")
    st.markdown("- Calculate each microgrid's solar balance, surplus and deficit.\n- Match feasible trades using a transparent negotiated-price rule.\n- Compare no-trading and trading costs without counting internal transfers as community savings.\n- Enumerate finite strategy profiles, calculate payoffs, best responses and pure Nash equilibria.\n- Export results for academic review.")
    st.write("**Microgrid:** a local energy system with generation, demand and potentially storage. **Game theory:** studies strategic choices where each participant's payoff depends on its own action and the actions of others.")
    st.success("Use the tabs to configure the simulation, inspect trades, analyze equilibria, and download CSV results.")

with pages[1]:
    st.subheader("Microgrid configuration")
    st.write("Edit the table below. Use 3–6 uniquely named microgrids. Prices are in ₹/kWh; energy is in kWh.")
    edited = st.data_editor(st.session_state.grid_data, num_rows="dynamic", use_container_width=True,
        column_config={"name": st.column_config.TextColumn("Name"),
          "solar_generation": st.column_config.NumberColumn("Solar generation (kWh)", min_value=0.0),
          "demand": st.column_config.NumberColumn("Demand (kWh)", min_value=0.0),
          "grid_price": st.column_config.NumberColumn("External grid price (₹/kWh)", min_value=0.0),
          "min_sell_price": st.column_config.NumberColumn("Minimum selling price (₹/kWh)", min_value=0.0),
          "battery_capacity": st.column_config.NumberColumn("Battery capacity (kWh; informational)", min_value=0.0)}, key="grid_editor")
    st.session_state.grid_data = edited
    try:
        if not 3 <= len(edited) <= 6:
            raise ValueError("Configure between 3 and 6 microgrids.")
        if edited["name"].astype(str).str.strip().eq("").any() or edited["name"].duplicated().any():
            raise ValueError("Names must be non-empty and unique.")
        grids = [Microgrid(str(r.name), float(r.solar_generation), float(r.demand), float(r.grid_price), float(r.min_sell_price), float(r.battery_capacity)) for r in edited.itertuples(index=False)]
        st.session_state.validation_error = ""
    except Exception as e:
        grids = []
        st.session_state.validation_error = str(e)
    if st.session_state.validation_error:
        st.error(st.session_state.validation_error)
    else:
        energy = pd.DataFrame([g.energy_balance() for g in grids])
        left, right = st.columns(2)
        left.plotly_chart(generation_demand_chart(grids), use_container_width=True)
        right.plotly_chart(balance_chart(grids), use_container_width=True)
        st.dataframe(energy, use_container_width=True)
        st.caption("Net energy = generation − demand; surplus = max(net, 0); deficit = max(−net, 0).")

# Rebuild validated grids on each rerun.
try:
    df = st.session_state.grid_data
    if not 3 <= len(df) <= 6 or df["name"].astype(str).str.strip().eq("").any() or df["name"].duplicated().any():
        raise ValueError("Configure 3–6 microgrids with unique non-empty names in the Configure tab.")
    grids = [Microgrid(str(r.name), float(r.solar_generation), float(r.demand), float(r.grid_price), float(r.min_sell_price), float(r.battery_capacity)) for r in df.itertuples(index=False)]
    validation_error = ""
except Exception as exc:
    grids, validation_error = [], str(exc)

if grids:
    transactions = match_energy(grids)
    individual, community = analyze_results(grids, transactions)
    strategy_table, equilibria = find_pure_nash_equilibria(grids)
else:
    transactions, individual, community = [], pd.DataFrame(), pd.DataFrame()
    strategy_table, equilibria = pd.DataFrame(), pd.DataFrame()

with pages[2]:
    st.subheader("Trading marketplace")
    if validation_error:
        st.warning(validation_error)
    else:
        tx_df = transactions_frame(transactions)
        if tx_df.empty:
            st.info("No feasible trades are available for this configuration.")
        else:
            st.dataframe(tx_df, use_container_width=True)
            st.metric("Total energy traded", f"{sum(t.energy_kwh for t in transactions):.2f} kWh")
        st.plotly_chart(network_chart(grids, transactions), use_container_width=True)
        st.write("**Pricing rule:** each feasible trade uses the midpoint of the seller's minimum acceptable price and the buyer's avoided external-grid price. If the seller minimum exceeds the buyer's grid price, no trade occurs between that pair.")
        rem = []
        for g in grids:
            sold = sum(t.energy_kwh for t in transactions if t.seller == g.name)
            bought = sum(t.energy_kwh for t in transactions if t.buyer == g.name)
            rem.append({"Microgrid": g.name, "Remaining surplus (kWh)": max(g.surplus-sold, 0), "Remaining deficit (kWh)": max(g.deficit-bought, 0)})
        st.dataframe(pd.DataFrame(rem), use_container_width=True)

with pages[3]:
    st.subheader("Finite non-cooperative game")
    st.write("Each microgrid chooses a participation fraction of its own surplus/deficit: **Abstain (0%)**, **Cautious (50%)**, or **Full (100%)**. The marketplace is rerun for every profile. Payoff is the participant's net financial benefit relative to the no-trade baseline. The game is evaluated independently of the full-participation marketplace result.")
    st.code("Players: configured microgrids\nStrategies per player: {0%, 50%, 100% participation}\nPayoff: baseline external-grid cost − participant net cost after internal trades\nBest response: strategy with maximum payoff given the other players' strategies\nPure Nash equilibrium: no player can improve payoff by unilateral deviation", language="text")
    if validation_error:
        st.warning(validation_error)
    else:
        st.metric("Profiles enumerated", f"{len(strategy_table):,}")
        if equilibria.empty:
            st.warning("No pure-strategy Nash equilibrium exists in this finite game.")
        else:
            st.success(f"Found {len(equilibria)} pure-strategy Nash equilibrium/equilibria.")
            st.dataframe(equilibria, use_container_width=True)
        st.markdown("**Strategy profile explorer**")
        cols = st.columns(min(len(grids), 3))
        selected = []
        for i, g in enumerate(grids):
            with cols[i % len(cols)]:
                selected.append(st.selectbox(f"{g.name} strategy", list(STRATEGIES), index=2, key=f"strat_{g.name}"))
        profile = tuple(selected)
        payoffs = profile_payoffs(grids, profile)
        st.write("Payoffs for selected profile:", {g.name: round(p, 2) for g, p in zip(grids, payoffs)})
        for i, g in enumerate(grids):
            br = best_responses(lambda p: profile_payoffs(grids, p), profile, i)
            st.write(f"**{g.name} best response(s):** {', '.join(br)}" + (" — currently a best response." if selected[i] in br else " — current strategy is not a best response."))
        st.plotly_chart(payoff_chart(strategy_table, grids), use_container_width=True)
        st.caption("A successful trade is not itself proof of equilibrium. This model checks all unilateral deviations for every enumerated profile. The pure-equilibrium search is exhaustive for this finite strategy space.")

with pages[4]:
    st.subheader("Financial and community results")
    if validation_error:
        st.warning(validation_error)
    else:
        m = {r["Metric"]: r["Value"] for r in community.to_dict("records")}
        cols = st.columns(4)
        cols[0].metric("Energy traded", f"{m['Total energy traded (kWh)']:.2f} kWh")
        cols[1].metric("Community cost savings", f"₹{m['Community operating-cost savings (₹)']:.2f}")
        cols[2].metric("Grid purchases after", f"{m['External-grid purchases after trading (kWh)']:.2f} kWh")
        cols[3].metric("Renewable utilization", f"{m['Renewable utilization rate (%)']:.1f}%")
        st.dataframe(individual, use_container_width=True)
        st.dataframe(community, use_container_width=True)
        st.plotly_chart(cost_chart(individual), use_container_width=True)
        st.plotly_chart(savings_chart(individual), use_container_width=True)
        st.info("Community cost includes external-grid energy purchases only. Internal buyer payments and seller revenues cancel across the community and are not counted as community savings. Individual net cost includes their payments/revenues.")
        st.download_button("Download transactions.csv", transactions_frame(transactions).to_csv(index=False).encode("utf-8-sig"), "transactions.csv", "text/csv")
        st.download_button("Download individual_results.csv", individual.to_csv(index=False).encode("utf-8-sig"), "individual_results.csv", "text/csv")
        st.download_button("Download community_metrics.csv", community.to_csv(index=False).encode("utf-8-sig"), "community_metrics.csv", "text/csv")
        st.download_button("Download game_strategy_profiles.csv", strategy_table.to_csv(index=False).encode("utf-8-sig"), "game_strategy_profiles.csv", "text/csv")
        st.download_button("Download pure_nash_equilibria.csv", equilibria.to_csv(index=False).encode("utf-8-sig"), "pure_nash_equilibria.csv", "text/csv")

with pages[5]:
    st.subheader("Mathematical model and assumptions")
    st.latex(r"E_i = G_i - D_i")
    st.latex(r"S_i = \max(E_i,0), \qquad B_i = \max(-E_i,0)")
    st.latex(r"0 \leq \sum_j q_{ij} \leq S_i, \qquad 0 \leq \sum_i q_{ij} \leq B_j")
    st.latex(r"T_{ij}=q_{ij}p_{ij}, \qquad p_{ij}=\frac{p_i^{min}+p_j^{grid}}{2}")
    st.markdown("**Assumptions**\n- One simulation time-step; energy is treated as directly transferable within the community.\n- No network losses, capacity bottlenecks, taxes, tariffs, or transaction fees.\n- Direct solar trading only; battery capacity is recorded but battery state-of-charge and dispatch are not simulated.\n- The greedy matching rule is deterministic, not claimed to be globally optimal.\n- Strategies are finite participation fractions; prices are determined by the midpoint rule rather than chosen strategically.\n- Nash equilibrium applies only to this defined finite game and its modeled payoffs, not to all real-world electricity markets.")
    st.markdown("**Workflow**\n```mermaid\nflowchart TD\n A[Configure microgrids] --> B[Compute surplus and deficit]\n B --> C[Match feasible sellers and buyers]\n C --> D[Calculate transaction and cost accounts]\n B --> E[Enumerate strategy profiles]\n E --> F[Calculate payoffs and best responses]\n F --> G[Verify pure Nash equilibria]\n D --> H[Dashboard, charts and CSV exports]\n G --> H\n```\n\n**Architecture**\n```mermaid\nflowchart LR\n UI[Streamlit app.py] --> MODEL[microgrid.py]\n UI --> MARKET[trading.py]\n UI --> GAME[game_theory.py]\n UI --> FIN[analysis.py]\n UI --> VIZ[visualization.py]\n DATA[sample_data.py] --> UI\n MARKET --> FIN\n MARKET --> GAME\n FIN --> VIZ\n```")

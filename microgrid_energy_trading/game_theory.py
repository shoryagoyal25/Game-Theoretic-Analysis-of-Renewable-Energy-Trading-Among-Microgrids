"""Finite non-cooperative participation game and pure Nash equilibrium solver.

Each player selects one of three quantity strategies: abstain (0%), cautious (50%),
 or full participation (100%) of their own initial surplus/deficit. The marketplace
matches these offered quantities at deterministic feasible midpoint prices. Payoff is
individual economic benefit relative to the no-trading baseline. Since internal payments
are transfers, the sum of player payoffs need not equal community operating-cost savings.
"""
from itertools import product
from typing import Callable, Sequence
import pandas as pd
from microgrid import Microgrid
from trading import match_energy
from analysis import analyze_results

STRATEGIES: dict[str, float] = {"Abstain (0%)": 0.0, "Cautious (50%)": 0.5, "Full (100%)": 1.0}


def profile_payoffs(microgrids: list[Microgrid], profile: tuple[str, ...]) -> tuple[float, ...]:
    if len(profile) != len(microgrids) or any(s not in STRATEGIES for s in profile):
        raise ValueError("Profile must assign one valid strategy to every microgrid.")
    fractions = {g.name: STRATEGIES[s] for g, s in zip(microgrids, profile)}
    sellers = {g.name: fractions[g.name] for g in microgrids}
    buyers = {g.name: fractions[g.name] for g in microgrids}
    tx = match_energy(microgrids, sellers, buyers)
    individual, _ = analyze_results(microgrids, tx)
    return tuple(float(individual.loc[individual["Microgrid"] == g.name, "Net Individual Savings (₹)"].iloc[0])
                 for g in microgrids)


def best_responses(payoff: Callable[[tuple[str, ...]], tuple[float, ...]],
                   profile: tuple[str, ...], player_index: int,
                   strategies: Sequence[str] = tuple(STRATEGIES)) -> list[str]:
    values = []
    for strategy in strategies:
        candidate = list(profile)
        candidate[player_index] = strategy
        values.append((payoff(tuple(candidate))[player_index], strategy))
    best = max(v for v, _ in values)
    return [s for v, s in values if abs(v - best) <= 1e-9]


def is_nash_equilibrium(payoff: Callable[[tuple[str, ...]], tuple[float, ...]],
                        profile: tuple[str, ...], strategies: Sequence[str] = tuple(STRATEGIES)) -> bool:
    current = payoff(profile)
    for i in range(len(profile)):
        for strategy in strategies:
            if strategy == profile[i]:
                continue
            candidate = list(profile)
            candidate[i] = strategy
            if payoff(tuple(candidate))[i] > current[i] + 1e-9:
                return False
    return True


def find_pure_nash_equilibria(microgrids: list[Microgrid]) -> tuple[pd.DataFrame, pd.DataFrame]:
    strategy_names = tuple(STRATEGIES)
    cache: dict[tuple[str, ...], tuple[float, ...]] = {}
    def payoff(profile: tuple[str, ...]) -> tuple[float, ...]:
        if profile not in cache:
            cache[profile] = profile_payoffs(microgrids, profile)
        return cache[profile]
    rows = []
    equilibria = []
    for profile in product(strategy_names, repeat=len(microgrids)):
        payoffs = payoff(profile)
        eq = is_nash_equilibrium(payoff, profile, strategy_names)
        row = {g.name + " Strategy": s for g, s in zip(microgrids, profile)}
        row.update({g.name + " Payoff (₹)": round(v, 4) for g, v in zip(microgrids, payoffs)})
        row["Pure Nash Equilibrium"] = eq
        rows.append(row)
        if eq:
            equilibria.append(row)
    return pd.DataFrame(rows), pd.DataFrame(equilibria, columns=list(rows[0].keys()) if rows else [])


def matching_pennies_payoff(profile: tuple[str, str]) -> tuple[float, float]:
    """Known no-pure-equilibrium test game (matching pennies)."""
    if len(profile) != 2 or any(s not in ("Heads", "Tails") for s in profile):
        raise ValueError("Use Heads/Tails for both players.")
    same = profile[0] == profile[1]
    return (1.0, -1.0) if same else (-1.0, 1.0)

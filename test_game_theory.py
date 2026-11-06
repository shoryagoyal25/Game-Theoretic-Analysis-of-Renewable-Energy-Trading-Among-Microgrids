from itertools import product
from microgrid import Microgrid
from game_theory import STRATEGIES, best_responses, is_nash_equilibrium, matching_pennies_payoff, find_pure_nash_equilibria

def test_known_pure_equilibrium_coordination_game():
    def payoff(p):
        return (2, 2) if p == ("A", "A") else (0, 0) if p == ("B", "B") else (-1, -1)
    assert is_nash_equilibrium(payoff, ("A", "A"), ("A", "B"))
    assert is_nash_equilibrium(payoff, ("B", "B"), ("A", "B"))
    assert not is_nash_equilibrium(payoff, ("A", "B"), ("A", "B"))

def test_matching_pennies_has_no_pure_equilibrium():
    profiles = list(product(("Heads", "Tails"), repeat=2))
    assert not any(is_nash_equilibrium(matching_pennies_payoff, p, ("Heads", "Tails")) for p in profiles)

def test_best_response():
    def payoff(p):
        return (2 if p[0] == "A" else 1, 1)
    assert best_responses(payoff, ("B", "A"), 0, ("A", "B")) == ["A"]

def test_microgrid_game_enumerates_all_profiles_and_returns_equilibria():
    grids = [Microgrid("S", 30, 10, 10, 4), Microgrid("B", 5, 25, 12, 5), Microgrid("X", 10, 10, 11, 4)]
    all_profiles, equilibria = find_pure_nash_equilibria(grids)
    assert len(all_profiles) == len(STRATEGIES) ** len(grids)
    assert "Pure Nash Equilibrium" in all_profiles.columns
    assert all(equilibria["Pure Nash Equilibrium"])

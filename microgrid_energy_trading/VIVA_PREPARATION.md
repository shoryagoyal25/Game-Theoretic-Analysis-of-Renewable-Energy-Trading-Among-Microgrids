# Viva Preparation: Microgrid Renewable Energy Trading

## 1. What is the project about?
It simulates direct renewable electricity trades between microgrids, calculates individual and community costs, and studies strategic participation using a finite non-cooperative game.

## 2. What is a microgrid?
A local energy system that coordinates generation, demand, and potentially storage. In this project, each microgrid has solar generation, demand, a grid purchase price, and a minimum selling price.

## 3. What is net energy?
Net energy is solar generation minus demand: `E = G − D`. Positive values indicate surplus; negative values indicate deficit.

## 4. How are surplus and deficit calculated?
`S = max(E, 0)` and `B = max(−E, 0)`.

## 5. How are sellers and buyers matched?
Sellers are ordered by their minimum acceptable selling price and buyers by their avoided grid price. The algorithm allocates the minimum of remaining supply and remaining demand for each feasible pair.

## 6. How is the trade price set?
The midpoint rule is used: `(seller minimum price + buyer grid price) / 2`. A trade is feasible only if the seller's minimum price is no greater than the buyer's grid price.

## 7. Why can the project have no trades?
All seller minimum prices may be above the buyers' avoided grid prices, or no available surplus and deficit may overlap.

## 8. How do you ensure the seller does not oversell?
The matcher tracks remaining supply and only allocates up to the seller's remaining offered surplus. It asserts that total sales do not exceed available surplus.

## 9. How do you ensure a buyer does not overbuy?
The matcher tracks remaining demand and caps each allocation at the buyer's remaining deficit. It asserts that total purchases do not exceed available deficit.

## 10. What is game theory?
A mathematical framework for analyzing decisions made by participants whose outcomes depend on the decisions of other participants.

## 11. Who are the players and what are their strategies?
Each microgrid is a player. Each chooses Abstain (0%), Cautious (50%), or Full (100%) participation of its initial surplus or deficit.

## 12. What is a payoff in this project?
Each player's net financial benefit compared with the no-trading baseline, calculated from external-grid cost changes and internal sale revenues or purchase payments.

## 13. What is a best response?
A strategy that gives a player the highest payoff when the other players' strategies are fixed. There may be multiple best responses if payoffs tie.

## 14. What is a Nash equilibrium?
A strategy profile where no player can improve their payoff by changing their own strategy alone while other players keep theirs unchanged.

## 15. How does the code verify a Nash equilibrium?
It calculates the current profile's payoffs, changes each player's strategy one at a time to every alternative, and checks whether any unilateral deviation gives that player a strictly higher payoff. It exhaustively enumerates all profiles in the finite strategy space.

## 16. Why test matching pennies?
Matching pennies is a standard two-player game with no pure-strategy Nash equilibrium. It checks that the equilibrium verifier can correctly report that a pure equilibrium does not exist.

## 17. Why test a coordination game?
A coordination game provides known pure equilibria. It checks that the verifier correctly identifies profiles where neither player benefits from a unilateral deviation.

## 18. Does every successful trade imply a Nash equilibrium?
No. Marketplace matching is a physical/economic allocation rule. Nash equilibrium is a separate strategic stability property and must be verified by checking deviations.

## 19. What is the difference between individual savings and community savings?
Individual net savings include the participant's own payment or revenue. Community operating-cost savings count reduced external-grid purchases only; internal payments and revenues cancel as transfers within the community.

## 20. Why might one participant have negative net savings?
A participant may pay for internal energy or have a price/quantity combination that does not improve its own modeled net cost. Individual incentives can differ from community-wide cost reduction.

## 21. Why is the matching algorithm greedy?
It is easy to explain, deterministic, fast, and suitable for a small educational simulation. It is not guaranteed to find a globally optimal allocation for every market configuration.

## 22. Are batteries implemented?
Battery capacity is accepted as an informational input, but battery dispatch, state of charge, charging/discharging power, and efficiency are not modeled in this version.

## 23. What are the major assumptions?
One time step, no network losses or line limits, direct energy transfer, no taxes or fees, midpoint transaction pricing, and a finite participation strategy space.

## 24. What is renewable utilization rate in the dashboard?
It is the simplified aggregate indicator `min(total generation, total demand) / total generation × 100`. It is not a full time-series self-consumption or grid-impact metric.

## 25. What can be improved in future?
Add batteries, multi-period data, uncertainty, network constraints, optimized dispatch, strategic bids/prices, mixed strategies, and comparisons with social-welfare optimization.

## 26. How do you run the project?
Create and activate a Python virtual environment, install packages with `pip install -r requirements.txt`, run `streamlit run app.py`, and execute tests with `pytest -q`.

## 27. What do the CSV files contain?
Transactions, individual microgrid results, community metrics, all game strategy profiles, and pure Nash equilibrium profiles.

## 28. Are the sample values real data?
No. They are illustrative simulated values chosen to demonstrate the algorithms; they are not measurements or published research results.

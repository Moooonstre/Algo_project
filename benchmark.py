"""Performance benchmark - exact vs greedy, and scaling of graph traversals.

Answers the project's "analyze the efficiency of your algorithms" requirement
and the labs' scaling questions (exact methods explode, greedy/linear scale).
Run from the repository root:

    python benchmark.py

Prints Markdown tables. Uses only the standard library (``time``).
"""

from __future__ import annotations

import time
from typing import Callable

from backend.datasets import random_social_graph
from backend.hard_problems import (
    fast_alternative_strategy,
    find_fast_coverage,
    find_max_invitations_exact,
    find_max_invitations_greedy,
    find_minimum_coverage,
    maximize_reach,
)


def _time(fn: Callable[[], object]) -> tuple[float, object]:
    start = time.perf_counter()
    result = fn()
    return (time.perf_counter() - start) * 1000.0, result  # ms


def bench_dominating_set() -> None:
    print("## Dominating set - exact (brute force) vs greedy\n")
    print("| N | exact (ms) | exact size | greedy (ms) | greedy size |")
    print("|---|-----------|-----------|------------|-------------|")
    for n in (5, 10, 15, 18):
        g = random_social_graph(n, edge_probability=0.3, seed=42)
        t_exact, (s_exact, _) = _time(lambda: find_minimum_coverage(g))
        t_greedy, (s_greedy, _) = _time(lambda: find_fast_coverage(g))
        print(
            f"| {n} | {t_exact:.2f} | {s_exact} | {t_greedy:.3f} | {s_greedy} |"
        )
    print()


def bench_independent_set() -> None:
    print("## Maximum independent set - exact (backtracking) vs greedy\n")
    print("| N | exact (ms) | exact size | greedy (ms) | greedy size |")
    print("|---|-----------|-----------|------------|-------------|")
    for n in (5, 10, 15, 20, 25):
        g = random_social_graph(n, edge_probability=0.3, seed=7)
        t_exact, (s_exact, _) = _time(lambda: find_max_invitations_exact(g))
        t_greedy, (s_greedy, _) = _time(lambda: find_max_invitations_greedy(g))
        print(
            f"| {n} | {t_exact:.2f} | {s_exact} | {t_greedy:.3f} | {s_greedy} |"
        )
    print()


def bench_knapsack() -> None:
    print("## 0/1 Knapsack - exact DP vs greedy ratio\n")
    print("| N | budget | DP (ms) | DP value | greedy (ms) | greedy value |")
    print("|---|--------|---------|----------|-------------|--------------|")
    import random as _r
    for n, budget in ((50, 100), (100, 500), (200, 1000), (300, 2000)):
        rng = _r.Random(1)
        costs = [rng.randint(1, 20) for _ in range(n)]
        infs = [rng.randint(1, 100) for _ in range(n)]
        t_dp, (v_dp, _) = _time(lambda: maximize_reach(budget, costs, infs))
        t_gr, (v_gr, _) = _time(lambda: fast_alternative_strategy(budget, costs, infs))
        print(
            f"| {n} | {budget} | {t_dp:.2f} | {v_dp} | {t_gr:.3f} | {v_gr} |"
        )
    print()


def main() -> None:
    print("# ASNAP - Performance benchmarks\n")
    print(
        "Exact methods solve NP-Hard problems optimally but explode with size; "
        "greedy/DP heuristics stay fast. Times in milliseconds.\n"
    )
    bench_dominating_set()
    bench_independent_set()
    bench_knapsack()


if __name__ == "__main__":
    main()

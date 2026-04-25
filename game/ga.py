"""Genetic algorithm for evolving enemy behaviour across dungeon runs."""
from __future__ import annotations
import random

# Gene definitions shared with entities/enemy.py
DEFAULT_GENES: dict[str, float] = {
    'aggression':       0.01,   # score weight: closer to player = better
    'anchor_weight':    10.0,   # bonus score for anchoring a limb
    'float_penalty':    5.0,    # penalty for failing to anchor
    'stability_weight': 2.0,    # bonus per other already-anchored limb
    'reach_min':        0.3,    # minimum reach as fraction of limb length
    'candidates':       24.0,   # candidate positions evaluated per move
    'weight':           1.0,    # heavier = more HP, slower movement
    'nail_length':      1.0,    # longer nails = greater hit range and damage
    'appendages':       1.0,    # more appendages = faster, but less HP and damage
}

GENE_BOUNDS: dict[str, tuple[float, float]] = {
    'aggression':       (0.002, 0.60),
    'anchor_weight':    (2.0,   20.0),
    'float_penalty':    (0.5,   15.0),
    'stability_weight': (0.0,    6.0),
    'reach_min':        (0.10,   0.90),
    'candidates':       (8.0,   64.0),
    'weight':           (0.5,   3.0),
    'nail_length':      (0.5,   3.0),
    'appendages':       (1.0,   4.0),
}


def enemy_fitness(enemy) -> float:
    """Reward damage dealt; penalise dying and taking damage."""
    score = enemy.damage_dealt * 3.0
    score -= (enemy.max_hp - enemy.hp) * 0.5
    if not enemy.alive:
        score -= 5.0
    return score


def evolve(
    gene_pool: list[dict[str, float]],
    fitnesses: list[float],
    rng: random.Random,
    total_deaths: int,
    size: int,
) -> list[dict[str, float]]:
    """Return a new generation of *size* genomes.

    Mutation pressure scales with cumulative enemy deaths so the GA becomes
    more exploratory (aggressive) as the player kills more enemies.
    """
    if not gene_pool:
        return [dict(DEFAULT_GENES) for _ in range(size)]

    # More deaths → higher mutation pressure
    mut_rate  = min(0.75, 0.10 + total_deaths * 0.012)
    mut_scale = min(0.45, 0.05 + total_deaths * 0.006)

    def _tournament() -> dict[str, float]:
        k = min(3, len(gene_pool))
        picks = rng.sample(range(len(gene_pool)), k)
        best  = max(picks, key=lambda i: fitnesses[i])
        return gene_pool[best]

    # Elitism: carry top 2 survivors unchanged
    order = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
    new_gen: list[dict[str, float]] = [
        dict(gene_pool[i]) for i in order[:min(2, len(order))]
    ]

    while len(new_gen) < size:
        pa, pb = _tournament(), _tournament()
        child = {k: (pa[k] if rng.random() < 0.5 else pb[k]) for k in DEFAULT_GENES}
        for key, (lo, hi) in GENE_BOUNDS.items():
            if rng.random() < mut_rate:
                child[key] = min(hi, max(lo, child[key] + rng.gauss(0, (hi - lo) * mut_scale)))
        new_gen.append(child)

    return new_gen

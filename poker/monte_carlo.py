from dataclasses import dataclass, asdict
from random import Random
from threading import Event
from math import sqrt
from treys import Evaluator
from .deck import validate_cards, remaining_deck
from .hand_evaluator import ENCODED
from .opponent_ranges import parse_range

class SimulationCancelled(Exception):
    pass

@dataclass(frozen=True)
class EquityResult:
    win: float
    tie: float
    loss: float
    equity: float
    simulations: int
    standard_error: float
    ranges: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)

def simulate(hole, board=(), opponents: int = 1, simulations: int = 10000,
             ranges: tuple[str, ...] = (), seed: int | None = None,
             cancel: Event | None = None, progress=None) -> EquityResult:
    hole, board = validate_cards(hole, board)
    if type(opponents) is not int or not 1 <= opponents <= 8:
        raise ValueError("Number of opponents must be 1–8")
    if type(simulations) is not int or not 1 <= simulations <= 1000000:
        raise ValueError("Simulation count must be 1–1,000,000")
    ranges = tuple(ranges) or ("Random",) * opponents
    if len(ranges) == 1:
        ranges *= opponents
    if len(ranges) != opponents:
        raise ValueError("Provide one range or one per opponent")
    known = set(hole + board)
    choices = [tuple(c for c in parse_range(r) if not known.intersection(c)) for r in ranges]
    if any(not c for c in choices):
        raise ValueError("An opponent range has no combinations after blockers")
    rng, evaluator = Random(seed), Evaluator()
    deck = remaining_deck(hole + board)
    hero = [ENCODED[c] for c in hole]
    wins = ties = 0
    share = share2 = 0.0
    # Independent draws + rejection preserve the joint range distribution.
    # Sequentially renormalizing each player's range biases multiway results.
    attempts = 0
    for iteration in range(simulations):
        while True:
            if cancel is not None and cancel.is_set():
                raise SimulationCancelled()
            holdings = [rng.choice(c) for c in choices]
            flat = [card for hand in holdings for card in hand]
            attempts += 1
            if len(set(flat)) == 2 * opponents:
                break
            if attempts > max(100000, simulations * 100):
                raise ValueError("Ranges are incompatible or overlap too heavily; broaden them")
        available = [c for c in deck if c not in flat]
        runout = board + tuple(rng.sample(available, 5 - len(board)))
        encoded_board = [ENCODED[c] for c in runout]
        scores = [evaluator.evaluate(encoded_board, hero)]
        scores += [evaluator.evaluate(encoded_board, [ENCODED[c] for c in hand]) for hand in holdings]
        best = min(scores)
        fraction = 0.0
        if scores[0] == best:
            count = scores.count(best)
            wins += count == 1
            ties += count > 1
            fraction = 1 / count
        share += fraction
        share2 += fraction * fraction
        if progress and (iteration + 1) % 250 == 0:
            progress(iteration + 1, simulations)
    equity = share / simulations
    variance = max(0.0, (share2 - simulations * equity**2) / max(1, simulations - 1))
    return EquityResult(wins / simulations, ties / simulations,
                        (simulations-wins-ties) / simulations, equity,
                        simulations, sqrt(variance / simulations), ranges)

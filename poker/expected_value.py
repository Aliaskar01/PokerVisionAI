from .pot_odds import amount, SidePot
from math import isfinite

def probability(value: float) -> float:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Probability must be between 0 and 1")
    return value

def call_ev(equity: float, pot: float, call: float) -> float:
    return probability(equity) * (amount(pot) + amount(call)) - call

def aggression_ev(equity_when_called: float, pot: float, investment: float,
                  opponent_additional: float, fold_probability: float, effective_stack: float) -> float:
    """Heads-up terminal model: villain folds or calls, never reraises."""
    e, f = probability(equity_when_called), probability(fold_probability)
    pot, investment, extra, stack = map(amount, (pot, investment, opponent_additional, effective_stack))
    if investment > stack:
        raise ValueError("Investment exceeds effective stack")
    return f * pot + (1-f) * (e * (pot + investment + extra) - investment)

def side_pot_ev(pots: list[SidePot], equities: list[float], hero: str, call: float) -> float:
    """Each equity must be calculated separately against that pot's eligible players.
    Pots here already include hero's final contribution.
    """
    if len(pots) != len(equities):
        raise ValueError("Supply separate equity for every side pot")
    return sum(p.amount * probability(e) for p, e in zip(pots, equities) if hero in p.eligible) - amount(call)

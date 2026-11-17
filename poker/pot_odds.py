from dataclasses import dataclass
from math import isfinite

def amount(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError("Amounts must be finite nonnegative numbers")
    return float(value)

def pot_odds(pot: float, call: float) -> float:
    pot, call = amount(pot), amount(call)
    return call / (pot + call) if call else 0.0

@dataclass(frozen=True)
class SidePot:
    amount: float
    eligible: tuple[str, ...]

def build_side_pots(contributions: dict[str, float], folded: set[str] | None = None) -> list[SidePot]:
    """Contributions include all streets; folded money remains in each pot.

    A sole contributor's unmatched excess is a refund, not a contested pot.
    """
    folded = folded or set()
    values = {p: amount(v) for p, v in contributions.items()}
    pots, previous = [], 0.0
    for level in sorted(set(values.values()) - {0.0}):
        contributors = [p for p, v in values.items() if v >= level]
        if len(contributors) > 1:
            eligible = tuple(p for p in contributors if p not in folded)
            if not eligible:
                raise ValueError("No eligible player in a side pot")
            pots.append(SidePot((level-previous)*len(contributors), eligible))
        previous = level
    return pots

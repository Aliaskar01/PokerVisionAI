from dataclasses import dataclass, asdict
from .expected_value import call_ev, aggression_ev
from .pot_odds import pot_odds
from .game_state import GameState

@dataclass
class Analysis:
    recommendation: str | None
    actions: dict
    explanation: str
    assumptions: list[str]
    confidence: str = "Conditional model"

    def to_dict(self):
        return asdict(self)

def analyze(state: GameState, equity: float, *, mode="offline", terminal=False,
            entire_pot_eligible=False, sizes=(), fold_probability=None,
            calling_equity=None) -> Analysis:
    if mode not in ("offline", "manual"):
        raise ValueError("Strategy analysis is available only in offline/manual mode")
    assumptions = ["Equity depends on selected opponent ranges: " + ", ".join(state.ranges),
                   "No rake, ICM, or future betting modeled."]
    if state.pot is None or state.call_amount is None:
        return Analysis(None, {}, "Enter pot and call amount to compare legal actions.", assumptions)
    call = state.call_amount
    actions = {"FOLD": {"ev": 0.0, "risk": "Forfeit the pot"}} if call else {"CHECK": {"ev": None, "risk": "Future action unknown"}}
    threshold = pot_odds(state.pot, call)
    actions["CALL" if call else "CHECK"] = {"ev": None, "pot_odds": threshold, "equity": equity,
                                              "risk": "Range uncertainty and future betting"}
    if state.hero_stack is not None and call > state.hero_stack:
        return Analysis(None, actions, "Call exceeds hero stack. Enter the actual all-in call and eligible pots.", assumptions)
    valid = terminal and entire_pot_eligible
    recommendation = None
    explanation = "Confirm no future betting and eligibility for the entire pot to obtain terminal-call EV. Side pots require per-pot equities."
    if valid:
        ev = call_ev(equity, state.pot, call)
        actions["CALL" if call else "CHECK"]["ev"] = ev
        recommendation = ("CALL" if ev >= 0 else "FOLD") if call else "CHECK"
        explanation = f"Equity {equity:.2%}; break-even threshold {threshold:.2%}. Terminal call EV {ev:+.2f}. This comparison is conditional, not a full-game optimum."
        assumptions.append("No further betting; hero is eligible for the entire modeled pot.")
    aggression = "RAISE" if call else "BET"
    actions[aggression] = {"ev": None, "risk": "Requires calling range, fold probability, stack, legal size and response model"}
    if sizes and valid and state.active_opponents == 1 and calling_equity is not None and fold_probability is not None and state.effective_stack is not None:
        assumptions.append("Heads-up: opponent only folds or calls. Equity supplied separately against calling range; sizes are additional hero investment. Verify minimum legal raise.")
        for size in sizes:
            if size <= call:
                raise ValueError("Bet/raise investment must exceed the call amount")
            actions[f"{aggression} {size:g}"] = {"ev": aggression_ev(calling_equity, state.pot, size, size-call, fold_probability, state.effective_stack), "risk": "Fold probability and calling range are assumptions"}
    return Analysis(recommendation, actions, explanation, assumptions)

"""Treys scores: smaller is stronger; all 5-card subsets are considered."""
from treys import Card as TreysCard, Evaluator
from .card import parse_cards

ENCODED = {r+s: TreysCard.new(r+s) for r in "23456789TJQKA" for s in "cdhs"}

class HandEvaluator:
    def __init__(self):
        self.engine = Evaluator()

    def evaluate(self, cards) -> int:
        cards = parse_cards(cards)
        if not 5 <= len(cards) <= 7:
            raise ValueError("Evaluation needs 5–7 distinct cards")
        return self.engine.evaluate([], [ENCODED[c] for c in cards])

    def describe(self, cards) -> str:
        score = self.evaluate(cards)
        return "Royal Flush" if score == 1 else self.engine.class_to_string(self.engine.get_rank_class(score))

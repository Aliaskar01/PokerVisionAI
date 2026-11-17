"""Unweighted combinations, uniformly sampled conditional on all card blockers."""
from itertools import combinations, product
import re
from .card import RANKS, SUITS
from .deck import DECK

PROFILES = {
    "Random": "random",
    "Tight": "99+,AJs+,KQs,AKo",
    "Standard": "66+,ATs+,KJs+,QJs,JTs,AJo+,KQo",
    "Loose": "22+,A2s+,K9s+,Q9s+,J9s+,T9s,98s,87s,76s,ATo+,KJo+,QJo",
}

def parse_range(expression: str) -> tuple[tuple[str, str], ...]:
    expression = PROFILES.get(expression, expression).strip()
    if expression.lower() == "random":
        return tuple(combinations(DECK, 2))
    result = set()
    for token in re.split(r"[\s,;]+", expression):
        if not token:
            continue
        exact = re.fullmatch(r"([2-9TJQKA][cdhs])([2-9TJQKA][cdhs])", token)
        if exact:
            a, b = exact.groups()
            if a == b:
                raise ValueError("Range contains duplicate card")
            result.add(tuple(sorted((a, b))))
            continue
        match = re.fullmatch(r"([2-9TJQKA])([2-9TJQKA])([so]?)(\+?)", token)
        if not match:
            raise ValueError(f"Unsupported range token: {token}")
        a, b, kind, plus = match.groups()
        ia, ib = RANKS.index(a), RANKS.index(b)
        if ia < ib or (a == b and kind):
            raise ValueError(f"Invalid range token: {token}")
        ranks = [(a, b)]
        if plus:
            ranks = [(r, r) for r in RANKS[ia:]] if a == b else [(a, r) for r in RANKS[ib:ia]]
        for ra, rb in ranks:
            for sa, sb in product(SUITS, repeat=2):
                if ra == rb and sa == sb:
                    continue
                if kind == "s" and sa != sb or kind == "o" and sa == sb:
                    continue
                result.add(tuple(sorted((ra+sa, rb+sb))))
    if not result:
        raise ValueError("Opponent range is empty")
    return tuple(sorted(result))

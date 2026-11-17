from .card import RANKS, SUITS, parse_cards

DECK = tuple(r + s for r in RANKS for s in SUITS)

def remaining_deck(known: tuple[str, ...]) -> tuple[str, ...]:
    known = parse_cards(known)
    return tuple(c for c in DECK if c not in known)

def validate_cards(hole, board, complete_hole: bool = True) -> tuple[tuple[str, ...], tuple[str, ...]]:
    hole, board = parse_cards(hole), parse_cards(board)
    if (complete_hole and len(hole) != 2) or len(hole) > 2:
        raise ValueError("Exactly two hole cards are required")
    if len(board) not in (0, 3, 4, 5):
        raise ValueError("Board must have 0, 3, 4 or 5 cards")
    parse_cards(hole + board)
    return hole, board

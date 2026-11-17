from dataclasses import dataclass
import re

RANKS = "23456789TJQKA"
SUITS = "cdhs"

@dataclass(frozen=True, order=True)
class Card:
    rank: str
    suit: str

    def __post_init__(self):
        if self.rank not in RANKS or len(self.rank) != 1 or self.suit not in SUITS or len(self.suit) != 1:
            raise ValueError(f"Invalid card: {self.rank}{self.suit}")

    def __str__(self) -> str:
        return self.rank + self.suit

    @classmethod
    def parse(cls, value: str) -> "Card":
        value = value.strip().replace("10", "T")
        for symbol, suit in zip("♣♦♥♠", "cdhs"):
            value = value.replace(symbol, suit)
        if len(value) != 2:
            raise ValueError(f"Invalid card {value!r}; use Ah, Ks, Td")
        return cls(value[0].upper(), value[1].lower())

def parse_cards(value: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    tokens = re.split(r"[\s,;]+", value.strip()) if isinstance(value, str) else value
    result = tuple(str(Card.parse(x)) for x in tokens if x)
    if len(set(result)) != len(result):
        raise ValueError("Duplicate cards are impossible")
    return result

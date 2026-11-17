from dataclasses import dataclass, field, asdict
from .deck import validate_cards
from .pot_odds import amount

@dataclass
class GameState:
    hole_cards: tuple[str, ...] = ()
    community_cards: tuple[str, ...] = ()
    pot: float | None = None
    hero_stack: float | None = None
    active_opponents: int | None = None
    call_amount: float | None = None
    effective_stack: float | None = None
    dealer_position: str | None = None
    current_bet: float | None = None
    detection_confidence: float = 0.0
    ui_state: str = "UNKNOWN"
    ranges: tuple[str, ...] = ("Random",)
    sources: dict[str, str] = field(default_factory=dict)
    players: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    game_type: str = "NLHE"
    board_known: bool = True
    visible_board_count: int | None = None

    def __post_init__(self):
        self.hole_cards, self.community_cards = validate_cards(self.hole_cards, self.community_cards, False)
        self.ranges = tuple(self.ranges)
        for name in ("pot", "hero_stack", "call_amount", "effective_stack", "current_bet"):
            if getattr(self, name) is not None:
                amount(getattr(self, name))
        if self.active_opponents is not None and (type(self.active_opponents) is not int or not 0 <= self.active_opponents <= 8):
            raise ValueError("Opponents must be 0–8 or unknown")
        if not 0 <= self.detection_confidence <= 1:
            raise ValueError("Confidence must be 0–1")

    @property
    def street(self) -> str:
        count = len(self.community_cards) if self.board_known else self.visible_board_count
        return {0: "PREFLOP", 3: "FLOP", 4: "TURN", 5: "RIVER"}.get(count,'UNKNOWN')

    def equity_key(self) -> tuple:
        return self.hole_cards, self.community_cards, self.active_opponents, self.ranges,self.board_known,self.visible_board_count

    def to_dict(self) -> dict:
        return asdict(self) | {"street": self.street}

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        return cls(**{k: v for k, v in data.items() if k != "street"})

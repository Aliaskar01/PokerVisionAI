from dataclasses import dataclass
from uuid import uuid4
from poker.game_state import GameState

@dataclass
class TrackingUpdate:
    state: GameState | None
    hand_id: str
    changed: bool
    recalculate: bool
    new_hand: bool = False

class StateTracker:
    def __init__(self, consistent_frames=3):
        self.required = consistent_frames
        self.current = None
        self.pending = None
        self.count = 0
        self.hand_id = str(uuid4())
        self.finished = False

    def update(self, state: GameState, valid=True) -> TrackingUpdate:
        if not valid:
            self.pending, self.count = None,0
            return TrackingUpdate(self.current,self.hand_id,False,False)
        key = state.equity_key()
        evidence_key = (key,state.ui_state)
        if evidence_key == self.pending:
            self.count += 1
        else:
            self.pending, self.count = evidence_key,1
        if self.count < self.required:
            return TrackingUpdate(self.current,self.hand_id,False,False)
        if state.ui_state == 'HAND_FINISHED':
            self.finished = True
        old = self.current
        new_hand = old is not None and (state.hole_cards != old.hole_cards or
                    len(state.community_cards)<len(old.community_cards) or
                    (self.finished and state.ui_state != 'HAND_FINISHED'))
        if old and not new_hand and old.community_cards and state.community_cards[:len(old.community_cards)] != old.community_cards:
            # Never join incompatible boards into a single hand.
            new_hand = True
        if new_hand:
            self.hand_id = str(uuid4())
            self.finished = False
        self.current = state
        return TrackingUpdate(state,self.hand_id,old != state,old is None or old.equity_key()!=key or new_hand,new_hand)

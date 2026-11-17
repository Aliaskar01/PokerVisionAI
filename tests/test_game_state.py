import pytest
from poker.game_state import GameState

def test_state():
    s = GameState(hole_cards=('Jc','4h'),community_cards=('Jd','2d','Qc'))
    assert s.street == 'FLOP'
    assert GameState.from_dict(s.to_dict()) == s
    for board in [('2c',), ('2c','3d'), ('Jc','2d','Qc')]:
        with pytest.raises(ValueError):
            GameState(hole_cards=('Jc','4h'),community_cards=board)

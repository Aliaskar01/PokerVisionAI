import pytest
from poker.game_state import GameState
from poker.strategy_engine import analyze

def test_guards():
    s = GameState(pot=100,call_amount=20,active_opponents=1)
    with pytest.raises(ValueError):
        analyze(s,.5,mode='live')
    assert analyze(s,.5).recommendation is None
    assert analyze(s,.5,terminal=True,entire_pot_eligible=True).recommendation == 'CALL'
    assert analyze(s,.01,terminal=True,entire_pot_eligible=True).recommendation == 'FOLD'
    assert analyze(GameState(),.5).recommendation is None

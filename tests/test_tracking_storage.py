from dataclasses import replace
import json
from poker.game_state import GameState
from tracking.state_tracker import StateTracker
from storage.repository import Repository

def accept(tracker,state):
    for _ in range(3):
        result = tracker.update(state)
    return result

def test_transitions():
    tracker = StateTracker()
    s = GameState(hole_cards=('Ah','Kh'),active_opponents=1)
    assert tracker.update(s).state is None
    accept(tracker,s)
    original_id = tracker.hand_id
    s = replace(s,community_cards=('Qh','Jh','2c'))
    assert accept(tracker,s).state.street == 'FLOP'
    assert tracker.hand_id == original_id
    assert not accept(tracker,replace(s,pot=100)).recalculate
    tracker.update(replace(s,community_cards=()),valid=False)
    assert tracker.hand_id == original_id
    accept(tracker,replace(s,community_cards=()))
    assert tracker.hand_id != original_id

def test_roundtrip(tmp_path):
    repo = Repository(tmp_path/'test.db')
    state = GameState(hole_cards=('Ah','Kh'),sources={'hole_cards':'manual'})
    identifier = repo.save(state,corrections=[{'field':'hole_cards','value':'Ah Kh'}])
    assert GameState.from_dict(repo.get(identifier)['state']) == state
    repo.export(identifier,tmp_path/'hand.json')
    repo.export(identifier,tmp_path/'hand.csv')
    assert json.loads((tmp_path/'hand.json').read_text())['corrections']
    assert 'hole_cards' in (tmp_path/'hand.csv').read_text(encoding='utf-8-sig')
    repo.close()

def test_finished_marker_does_not_split_every_frame():
    tracker = StateTracker()
    s = GameState(hole_cards=('Ah','Kh'),ui_state='HAND_FINISHED')
    accept(tracker,s)
    hand = tracker.hand_id
    accept(tracker,s)
    assert tracker.hand_id == hand
    accept(tracker,replace(s,ui_state='WAITING_FOR_TURN'))
    assert tracker.hand_id != hand

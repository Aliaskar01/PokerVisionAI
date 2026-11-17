import pytest
from poker.pot_odds import pot_odds, build_side_pots
from poker.expected_value import call_ev, aggression_ev, side_pot_ev

def test_amounts():
    assert pot_odds(1000,200) == pytest.approx(1/6)
    assert pot_odds(0,0) == 0
    assert pot_odds(10,1000) == pytest.approx(1000/1010)
    for invalid in [-1, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            pot_odds(invalid, 1)
    assert call_ev(.5,100,20) == 40
    assert aggression_ev(.5,100,50,50,.2,100) == 60

def test_side_pots():
    pots = build_side_pots({'hero':50,'a':100,'b':150}, {'b'})
    assert [p.amount for p in pots] == [150,100]
    assert pots[0].eligible == ('hero','a')
    assert pots[1].eligible == ('a',)
    assert side_pot_ev(pots,[.5,0], 'hero',50) == 25

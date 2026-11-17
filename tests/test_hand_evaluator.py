import pytest
from poker.hand_evaluator import HandEvaluator

@pytest.mark.parametrize('cards,name', [
    ('Ah Kh Qh Jh Th 2c 3d', 'Royal Flush'),
    ('9h 8h 7h 6h 5h Ac Kc', 'Straight Flush'),
    ('As Ah Ad Ac Ks 2c 3h', 'Four of a Kind'),
    ('As Ah Ad Ks Kh 2c 3h', 'Full House'),
    ('Ah Jh 8h 6h 2h Kc Qc', 'Flush'),
    ('Ah 2d 3s 4h 5c Qd Jc', 'Straight'),
    ('As Ah Ad Ks Qh 2c 3h', 'Three of a Kind'),
    ('As Ah Kd Ks Qh 2c 3h', 'Two Pair'),
    ('As Ah Jd Ks Qh 2c 3h', 'Pair'),
    ('As 9h Jd Ks 7h 2c 3h', 'High Card'),
])
def test_categories(cards, name):
    assert HandEvaluator().describe(cards) == name

def test_kicker_and_split():
    e = HandEvaluator()
    assert e.evaluate('Ah Ad Ks Qc Js') < e.evaluate('As Ac Kh Qh Ts')
    assert e.evaluate('Ah Ad Ks Qc Js') == e.evaluate('As Ac Kh Qh Jd')
    with pytest.raises(ValueError):
        e.evaluate('Ah Ah Ks Qc Js')

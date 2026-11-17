from poker.equity_calculator import EquityCalculator
from poker.opponent_ranges import parse_range

def test_ranges():
    assert len(parse_range('AA')) == 6
    assert len(parse_range('AKs')) == 4
    assert len(parse_range('AKo')) == 12
    assert len(parse_range('77+')) == 48
    assert len(parse_range('AJs+')) == 12
    assert len(parse_range('Random')) == 1326
    assert len(parse_range('AA,AA')) == 6

def test_cache():
    c = EquityCalculator()
    a = c.calculate(('Ah','Kh'), simulations=10, seed=1)
    assert a is c.calculate(('Kh','Ah'), simulations=10, seed=1)

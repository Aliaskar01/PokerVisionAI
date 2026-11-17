import pytest
from threading import Event
from poker.monte_carlo import simulate, SimulationCancelled

def test_preflop():
    result = simulate(('As','Ah'), opponents=1, simulations=2500, seed=17)
    assert .80 < result.equity < .89
    assert result.win + result.tie + result.loss == pytest.approx(1)

@pytest.mark.parametrize('board', [('2c','7d','9h'),('2c','7d','9h','Js'),('2c','7d','9h','Js','Qd')])
def test_streets(board):
    r = simulate(('As','Ah'), board, 3, 150, seed=18)
    assert 0 <= r.win <= r.equity <= r.win + r.tie <= 1
    assert r == simulate(('As','Ah'), board, 3, 150, seed=18)

@pytest.mark.parametrize('opponents', [1, 2, 8])
def test_board_royal_split(opponents):
    r = simulate(('2c','3d'), ('As','Ks','Qs','Js','Ts'), opponents, 50, seed=7)
    assert r.tie == 1
    assert r.equity == pytest.approx(1/(opponents+1))

def test_known_villain_and_invalid():
    assert simulate(('Ah','Ad'), ('Ac','Ks','Qh','2c','3d'), ranges=('KhKd',), simulations=10).win == 1
    for kwargs in [dict(hole=('Ah','Ah')), dict(hole=('Ah','Ad'), opponents=9), dict(hole=('Ah','Ad'), board=('Ah','2s','3s')), dict(hole=('Ah','Ad'), ranges=('AA',), opponents=3, simulations=1)]:
        with pytest.raises(ValueError):
            simulate(**kwargs)

def test_cancel():
    stop = Event()
    stop.set()
    with pytest.raises(SimulationCancelled):
        simulate(('Ah','Kh'), cancel=stop)

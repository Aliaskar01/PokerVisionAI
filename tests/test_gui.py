import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt
from gui.main_window import MainWindow
from gui.dashboard import Dashboard
from poker.game_state import GameState

def test_window_and_sources(qtbot,tmp_path):
    window = MainWindow(tmp_path)
    qtbot.addWidget(window)
    window.show()
    assert window.tabs.count() == 3
    assert window.live.review is None
    assert window.windows.count() >= 0
    window.close()

def test_manual_probability_and_save(qtbot,tmp_path):
    window = MainWindow(tmp_path)
    qtbot.addWidget(window)
    panel = window.manual
    panel.form.simulations.setCurrentText('1000')
    panel.accept_state(GameState(hole_cards=('2c','3d'),community_cards=('As','Ks','Qs','Js','Ts'),active_opponents=2))
    panel.calculate()
    qtbot.waitUntil(lambda:panel.result is not None,timeout=10000)
    assert abs(panel.result.equity-1/3)<1e-10
    assert panel.probabilities.bars['tie'].value()==10000
    window.save(panel)
    assert window.repository.list()
    window.close()

def test_cancel_and_invalidate(qtbot):
    panel = Dashboard('manual')
    qtbot.addWidget(panel)
    panel.form.simulations.setCurrentText('100000')
    panel.accept_state(GameState(hole_cards=('Ah','Kh'),active_opponents=8))
    panel.calculate()
    panel.cancel()
    qtbot.waitUntil(lambda:not panel.workers,timeout=10000)
    assert panel.result is None
    panel.form.inputs['hole_cards'].setText('As Ks')
    assert panel.form.origins['hole_cards'].text() == 'Manual input'
    panel.shutdown()

def test_offline_synthetic_import(qtbot,tmp_path):
    window = MainWindow(tmp_path)
    qtbot.addWidget(window)
    window.demo()
    qtbot.waitUntil(lambda:window.offline.form.inputs['hole_cards'].text()=='Jc 4h',timeout=10000)
    assert window.offline.form.inputs['community_cards'].text() == 'Jd 2d Qc'
    window.close()

def test_rst_reference_import(qtbot,tmp_path):
    window = MainWindow(tmp_path)
    qtbot.addWidget(window)
    window.rst_demo()
    qtbot.waitUntil(lambda:window.offline.form.inputs['pot'].text()=='80',timeout=10000)
    assert window.offline.form.inputs['hole_cards'].text() == 'Jc 4h'
    assert window.offline.form.inputs['hero_stack'].text() == '380'
    assert window.latest_vision.state.ui_state == 'PRE_ACTION_AVAILABLE'
    window.close()

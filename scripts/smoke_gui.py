"""Offscreen GUI integration and a reviewable screenshot artifact."""
from pathlib import Path
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('POKERVISION_DATA',str(Path(__file__).resolve().parents[1]/'data/smoke'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from gui.main_window import MainWindow
from poker.game_state import GameState
from main import configure_app

app = QApplication([])
configure_app(app)
window = MainWindow()
window.show()
window.manual.form.simulations.setCurrentText('1000')
window.manual.accept_state(GameState(hole_cards=('Ah','Kh'),community_cards=('Qh','Jh','2c'),
    active_opponents=1,pot=1000,call_amount=200,hero_stack=2000,effective_stack=1500,
    sources={'hole_cards':'Manual input','community_cards':'Manual input','pot':'Manual input','call_amount':'Manual input','active_opponents':'Default assumption'}))
window.manual.review.terminal.setChecked(True)
window.manual.review.eligible.setChecked(True)
window.manual.calculate()
target = Path(__file__).resolve().parents[1]/'artifacts'
target.mkdir(exist_ok=True)
def finish():
    assert window.manual.result is not None,window.manual.status.text()
    window.grab().save(str(target/'manual-calculator.png'))
    window.close()
    app.quit()
QTimer.singleShot(2500,finish)
sys.exit(app.exec())

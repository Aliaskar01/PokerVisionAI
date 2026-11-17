"""Render the actual RST screenshot import and save recognized fields."""
from pathlib import Path
import os
import sys
import json
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('POKERVISION_DATA',str(Path(__file__).resolve().parents[1]/'data/rst-smoke'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from gui.main_window import MainWindow
from main import configure_app
from config import ROOT

app = QApplication([])
configure_app(app)
window = MainWindow()
window.show()
expected=[(('Qs','Th'),60,380),(('Jc','4h'),80,380),(('8c','5s'),1.5,44.5)]
index=1
started=time.monotonic()
window.load_path(ROOT/'assets/screenshots/rst_reference_1.png')
def check():
    global index,started
    if time.monotonic()-started>30:
        window.close()
        app.exit(1)
        return
    state=window.offline.form.state()
    hole,pot,stack=expected[index-1]
    if state.hole_cards==hole and state.pot==pot and state.hero_stack==stack and not window.offline.debounce.isActive():
        target=ROOT/'artifacts'
        target.mkdir(exist_ok=True)
        window.grab().save(str(target/f'rst-review-{index}.png'))
        (target/f'rst-recognition-{index}.json').write_text(json.dumps(state.to_dict(),indent=2),encoding='utf-8')
        if index==3:
            window.close()
            app.exit(0)
            return
        index+=1
        started=time.monotonic()
        window.load_path(ROOT/f'assets/screenshots/rst_reference_{index}.png')
    QTimer.singleShot(100,check)
QTimer.singleShot(100,check)
sys.exit(app.exec())

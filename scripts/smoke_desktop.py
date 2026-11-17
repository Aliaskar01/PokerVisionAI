"""Temporary synthetic window validates real Win32 + MSS capture; closes itself."""
from pathlib import Path
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('POKERVISION_DATA',str(Path(__file__).resolve().parents[1]/'data/native-smoke'))
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from capture.window_detector import list_windows
from capture.screen_capture import CaptureWorker
from config import ROOT
from main import configure_app

app = QApplication([])
configure_app(app)
source = QLabel()
source.setWindowTitle('PokerVision synthetic capture test')
source.setPixmap(QPixmap(str(ROOT/'assets/screenshots/synthetic_demo.png')).scaledToHeight(700))
source.show()
frames,errors = [],[]
worker = None
def begin():
    global worker
    handle = next(w.handle for w in list_windows() if w.title=='PokerVision synthetic capture test')
    worker = CaptureWorker(handle=handle,fps=10)
    worker.frame.connect(frames.append)
    worker.error.connect(errors.append)
    worker.start()
def finish():
    worker.stop()
    worker.wait(3000)
    artifact = ROOT/'artifacts'
    artifact.mkdir(exist_ok=True)
    if frames:
        import cv2
        cv2.imencode('.png',frames[-1])[1].tofile(artifact/'native-capture.png')
    ok = len(frames)>=5 and not errors
    (artifact/'native-capture.txt').write_text(f'{"PASS" if ok else "FAIL"}: {len(frames)} frames; errors={errors}',encoding='utf-8')
    source.close()
    app.exit(0 if ok else 1)
QTimer.singleShot(500,begin)
QTimer.singleShot(2500,finish)
sys.exit(app.exec())

"""Capture the real LetsView window through the app's live worker, read-only."""
from pathlib import Path
import os,sys,time,json,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
if '--fixture' in sys.argv or '--source' in sys.argv:
    os.environ.pop('QT_QPA_PLATFORM',None)
else:
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('POKERVISION_DATA',str(Path(__file__).resolve().parents[1]/'data/letsview-smoke'))
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import QTimer,Qt
from PySide6.QtGui import QPixmap
from capture.window_detector import list_windows,window_region
from gui.main_window import MainWindow
from main import configure_app
from config import ROOT
import cv2

app=QApplication([])
configure_app(app)
fixture=None
if '--source' in sys.argv:
    source=QLabel()
    source.setWindowTitle('PokerVision mirror capture fixture')
    pixmap=QPixmap(str(ROOT/'assets/screenshots/letsview_reference_4.png')).scaledToHeight(600,Qt.TransformationMode.SmoothTransformation)
    source.setPixmap(pixmap)
    source.setFixedSize(pixmap.size())
    source.show()
    QTimer.singleShot(200,lambda:print('READY',flush=True))
    QTimer.singleShot(60000,app.quit)
    raise SystemExit(app.exec())
if '--fixture' in sys.argv:
    fixture=subprocess.Popen([sys.executable,__file__,'--source'],stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert fixture.stdout.readline().strip()=='READY'
window=MainWindow()
window.tabs.setCurrentIndex(0)
window.show()
candidates=[]
for item in list_windows():
    if (fixture and item.title=='PokerVision mirror capture fixture') or (not fixture and 'letsview' in item.title.lower()):
        try:
            bounds=window_region(item.handle)
        except RuntimeError:
            continue
        if bounds['height']>bounds['width']*1.5:
            candidates.append(item)
if len(candidates)!=1:
    if fixture:
        fixture.terminate()
    window.close()
    raise SystemExit('Expected one portrait LetsView window')
window.start_source('live',handle=candidates[0].handle)
started=time.monotonic()
def check():
    if time.monotonic()-started>40:
        print('FAIL: '+window.statusBar().currentMessage(),flush=True)
        if window.last_frame is not None:
            cv2.imencode('.png',window.last_frame)[1].tofile(ROOT/'artifacts/letsview-live-failed-source.png')
        if window.latest_vision:
            print(window.latest_vision.state.to_dict(),window.latest_vision.viewport,flush=True)
        if fixture:
            fixture.terminate()
        window.close()
        app.exit(1)
        return
    result=window.latest_vision
    if result and result.viewport and window.live.form.inputs['pot'].text():
        if fixture and (window.live.form.inputs['pot'].text()!='4' or window.live.form.inputs['community_cards'].text()!='Qs 8c Jd'):
            QTimer.singleShot(200,check)
            return
        window.capture.pause_event.set()
        window.grab().save(str(ROOT/'artifacts/letsview-live.png'))
        cv2.imencode('.png',window.last_frame)[1].tofile(ROOT/'artifacts/letsview-live-source.png')
        (ROOT/'artifacts/letsview-live-state.json').write_text(json.dumps(window.live.form.state().to_dict(),indent=2),encoding='utf-8')
        print('PASS: '+('native fixture' if fixture else 'actual LetsView')+' live window capture, viewport detection and visible fields',flush=True)
        if fixture:
            fixture.terminate()
        window.close()
        app.exit(0)
        return
    QTimer.singleShot(200,check)
QTimer.singleShot(200,check)
raise SystemExit(app.exec())

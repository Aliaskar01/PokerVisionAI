"""PokerVision AI entry point. All capture is read-only."""
import sys
import logging
import os
from pathlib import Path

STYLE = '''
QWidget { background:#111827; color:#e2e8f0; font-family:Segoe UI; font-size:13px; }
QLineEdit,QComboBox,QPlainTextEdit,QTextEdit,QListWidget { background:#1e293b; border:1px solid #475569; border-radius:5px; padding:6px; }
QPushButton { background:#164e63; border:1px solid #0e7490; border-radius:5px; padding:7px 12px; }
QPushButton:hover { background:#0e7490; }
QTabBar::tab { padding:11px 22px; background:#1e293b; }
QTabBar::tab:selected { background:#115e59; color:#ccfbf1; }
QProgressBar { border:1px solid #334155; border-radius:5px; text-align:center; min-height:23px; }
QProgressBar::chunk { background:#0d9488; border-radius:4px; }
QScrollArea { border:0; }
QSplitter::handle { background:#334155; width:2px; }
'''

def configure_app(app):
    from PySide6.QtGui import QFontDatabase
    # The offscreen Windows Qt backend does not enumerate system fonts.
    if not QFontDatabase.families():
        font = Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/segoeui.ttf'
        if font.exists():
            QFontDatabase.addApplicationFont(str(font))
    app.setStyleSheet(STYLE)

def main():
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from config import DATA
    except ImportError as exc:
        print(f'Missing dependency: {exc}. Run python -m pip install -r requirements.txt',file=sys.stderr)
        return 1
    DATA.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=DATA/'app.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    app = QApplication(sys.argv)
    app.setApplicationName('PokerVisionAI')
    configure_app(app)
    window = MainWindow()
    window.show()
    if '--smoke-test' in sys.argv:
        from PySide6.QtCore import QTimer
        from poker.game_state import GameState
        window.manual.form.simulations.setCurrentText('1000')
        window.manual.accept_state(GameState(hole_cards=('2c','3d'),community_cards=('As','Ks','Qs','Js','Ts'),active_opponents=2))
        window.manual.calculate()
        def finish_smoke():
            ok = False
            try:
                result = window.manual.result
                assert result is not None and abs(result.equity-1/3)<1e-9
                from config import ROOT,rst_portrait_profile
                from vision.pipeline import VisionPipeline
                import cv2
                import numpy as np
                import json
                pipeline = VisionPipeline(rst_portrait_profile())
                observations = []
                expected = [(('Qs','Th'),('3d','Ad','4h'),60,380),
                            (('Jc','4h'),('Jd','2d','Qc'),80,380),
                            (('8c','5s'),(),1.5,44.5)]
                for index,(hole,board,pot,stack) in enumerate(expected,1):
                    reference = cv2.imdecode(np.fromfile(ROOT/f'assets/screenshots/rst_reference_{index}.png',np.uint8),cv2.IMREAD_COLOR)
                    observed = pipeline.process(reference).state
                    assert observed.hole_cards==hole and observed.community_cards==board and observed.board_known
                    assert observed.pot==pot and observed.hero_stack==stack
                    assert pipeline.ocr.backend=='rapidocr' and not pipeline.ocr.error
                    observations.append(observed.to_dict())
                mirror = cv2.imdecode(np.fromfile(ROOT/'assets/screenshots/letsview_reference_4.png',np.uint8),cv2.IMREAD_COLOR)
                mirror_result = pipeline.process(mirror)
                observed = mirror_result.state
                assert observed.hole_cards==('5s','4d') and observed.community_cards==('Qs','8c','Jd')
                assert observed.pot==4 and observed.hero_stack==18 and mirror_result.viewport[1]==50
                observations.append(observed.to_dict())
                # A spectator has a board but no known hero hand. Live mode must
                # still display the board and pot without producing equity.
                from dataclasses import replace
                from vision.pipeline import VisionResult
                window.tabs.setCurrentIndex(0)
                window.capture_target='live'
                partial=replace(observed,hole_cards=())
                window.vision_result(mirror,VisionResult(partial,mirror_result.boxes,False,mirror_result.regions),window.generation)
                assert window.live.form.inputs['community_cards'].text()=='Qs 8c Jd'
                assert window.live.form.inputs['pot'].text()=='4' and window.live.result is None
                (DATA/'smoke-recognition.json').write_text(json.dumps(observations,indent=2),encoding='utf-8')
                ok = True
            except Exception:
                logging.exception('Packaged smoke test failed')
            (DATA/'smoke-result.txt').write_text('PASS' if ok else 'FAIL',encoding='utf-8')
            window.grab().save(str(DATA/'smoke-window.png'))
            window.close()
            app.exit(0 if ok else 1)
        QTimer.singleShot(4000,finish_smoke)
    return app.exec()

if __name__ == '__main__':
    raise SystemExit(main())

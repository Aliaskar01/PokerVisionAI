from pathlib import Path
import json
import cv2
import numpy as np
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QTabWidget,QSplitter,
    QComboBox,QPushButton,QLabel,QFileDialog,QInputDialog,QMessageBox,QSlider,QDialog,QListWidget,QDialogButtonBox)
from config import DATA,ROOT,LayoutProfile,rst_portrait_profile,upgrade_builtin_profile
from capture.screen_capture import CaptureWorker
from capture.window_detector import list_windows
from poker.game_state import GameState
from tracking.state_tracker import StateTracker
from tracking.hand_history import HandHistory
from storage.repository import Repository
from .dashboard import Dashboard
from .video_preview import VideoPreview
from .settings_window import SettingsWindow
from .workers import VisionWorker

class MainWindow(QMainWindow):
    def __init__(self,data_dir: Path | None = None):
        super().__init__()
        self.setWindowTitle('PokerVision AI — Local poker study')
        self.resize(1400,900)
        self.data_dir = data_dir or DATA
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self.repository = Repository(self.data_dir/'hands.db')
        self.profile_path = self.data_dir/'layout.json'
        try:
            self.profile = LayoutProfile.load(self.profile_path) if self.profile_path.exists() else rst_portrait_profile()
            self.profile = upgrade_builtin_profile(self.profile)
        except (ValueError,TypeError,KeyError):
            self.profile = LayoutProfile()
        self.capture,self.last_frame,self.capture_target = None,None,None
        self.generation,self.closing = 0,False
        self.tracker = StateTracker()
        self.history = HandHistory(self.tracker.hand_id)
        self.last_saved = None
        self.latest_vision = None
        root = QWidget()
        layout = QVBoxLayout(root)
        heading = QLabel('POKERVISION AI   /   OBSERVE · CALCULATE · REVIEW')
        heading.setStyleSheet('font-size:20px;font-weight:700;padding:10px;color:#5eead4')
        layout.addWidget(heading)
        toolbar = QHBoxLayout()
        for text,callback in [('Detection layout',self.settings),('Add card template',self.add_template),
                              ('Saved hands',self.saved_hands),('Export last save',self.export)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.tabs = QTabWidget()
        self.live,self.manual,self.offline = Dashboard('live'),Dashboard('manual'),Dashboard('offline')
        self.live_preview,self.offline_preview = VideoPreview(),VideoPreview()
        live_page,live_left = self._page(self.live_preview,self.live)
        source_row = QHBoxLayout()
        self.windows = QComboBox()
        self.windows.setMinimumWidth(180)
        source_row.addWidget(self.windows,1)
        refresh = QPushButton('Refresh')
        refresh.clicked.connect(self.refresh_windows)
        source_row.addWidget(refresh)
        self.fps = QComboBox()
        self.fps.addItems(['5','10','15','30'])
        self.fps.setCurrentText('10')
        source_row.addWidget(self.fps)
        live_left.insertLayout(0,source_row)
        controls = QHBoxLayout()
        for text,callback in [('Capture window',self.start_window),('Region',self.start_region),('Pause / resume',self.pause),('Stop',self.stop_capture),('Save screenshot',self.screenshot)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            controls.addWidget(button)
        live_left.addLayout(controls)
        self.observation = QLabel('Window capture reads the mirror itself. Region capture requires an unobscured screen area. No game controls are sent.')
        self.observation.setWordWrap(True)
        live_left.addWidget(self.observation)
        review_page,review_left = self._page(self.offline_preview,self.offline)
        review_controls = QHBoxLayout()
        for text,callback in [('Load media',self.load_file),('RST reference',self.rst_demo),('Synthetic demo',self.demo),('Pause / resume',self.pause),('Save frame',self.screenshot)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            review_controls.addWidget(button)
        review_left.insertLayout(0,review_controls)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0,0)
        self.seek.sliderReleased.connect(self.seek_video)
        review_left.addWidget(self.seek)
        self.review_status = QLabel('Offline media only. Pause to edit a decision point; loading a new frame clears corrections.')
        self.review_status.setWordWrap(True)
        review_left.addWidget(self.review_status)
        self.tabs.addTab(live_page,'Live observation')
        self.tabs.addTab(self.manual,'Manual calculator')
        self.tabs.addTab(review_page,'Offline review')
        self.tabs.setCurrentIndex(1)
        self.tabs.currentChanged.connect(self.tab_changed)
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)
        self.statusBar().showMessage('All data stays local. RST screenshot calibration is required.')
        for panel in (self.live,self.manual,self.offline):
            panel.save_requested.connect(lambda p=panel:self.save(p))
        self.vision = VisionWorker(self.profile,self)
        self.vision.result.connect(self.vision_result)
        self.vision.failure.connect(self.show_status)
        self.vision.start()
        self.refresh_windows()

    def _page(self,preview,dashboard):
        splitter = QSplitter()
        left = QWidget()
        layout = QVBoxLayout(left)
        layout.addWidget(preview,1)
        splitter.addWidget(left)
        splitter.addWidget(dashboard)
        splitter.setSizes([630,730])
        return splitter,layout

    def show_status(self,message):
        self.statusBar().showMessage(message)

    def refresh_windows(self):
        self.windows.clear()
        try:
            for window in list_windows():
                if 'PokerVision AI' not in window.title:
                    self.windows.addItem(window.title,window.handle)
        except RuntimeError as exc:
            self.show_status(str(exc))

    def tab_changed(self,index):
        self.stop_capture()
        if index == 0:
            self.manual.cancel()
            self.offline.cancel()
        self.generation += 1

    def stop_capture(self):
        if self.capture:
            self.capture.stop()
            self.capture.wait(3000)
            if self.capture.isRunning():
                self.show_status('Source is still stopping; wait before choosing another source')
                return False
            self.capture.deleteLater()
            self.capture = None
        self.generation += 1
        return True

    def start_source(self,target,**kwargs):
        if not self.stop_capture():
            return
        self.capture_target = target
        self.generation += 1
        generation = self.generation
        self.tracker = StateTracker()
        self.history = HandHistory(self.tracker.hand_id)
        self.capture = CaptureWorker(**kwargs,fps=int(self.fps.currentText()),parent=self)
        self.capture.frame.connect(lambda frame,g=generation:self.frame_arrived(frame,g))
        self.capture.error.connect(self.source_error)
        self.capture.position.connect(self.video_position)
        self.capture.start()
        self.show_status('Capturing read-only source')

    def start_window(self):
        handle = self.windows.currentData()
        if handle is None:
            self.show_status('No capture window selected; refresh the list after opening the mirror')
            return
        self.start_source('live',handle=handle)

    def start_region(self):
        text,ok = QInputDialog.getText(self,'Screen region','left, top, width, height (physical screen pixels)',text='0, 0, 493, 1077')
        if not ok:
            return
        try:
            left,top,width,height = map(int,text.split(','))
            if width<=0 or height<=0:
                raise ValueError('Width and height must be positive')
            self.start_source('live',region=dict(left=left,top=top,width=width,height=height))
        except ValueError as exc:
            self.show_status(f'Invalid screen region: {exc}')

    def pause(self):
        if self.capture:
            if self.capture.pause_event.is_set():
                self.capture.pause_event.clear()
                self.show_status('Resumed')
            else:
                self.capture.pause_event.set()
                self.show_status('Paused — corrections apply to this decision point')

    def source_error(self,message):
        self.live.cancel()
        self.live.probabilities.clear()
        self.live.result = None
        self.observation.setText('SOURCE UNAVAILABLE · '+message)
        self.show_status(message)

    def frame_arrived(self,frame,generation):
        if generation != self.generation:
            return
        self.last_frame = frame
        preview = self.live_preview if self.capture_target=='live' else self.offline_preview
        preview.show_frame(frame)
        self.vision.submit(frame,generation)

    def vision_result(self,frame,result,generation):
        if generation != self.generation or self.closing:
            return
        self.latest_vision = result
        if self.capture_target == 'live':
            self.live_preview.show_frame(frame,result.boxes,result.regions)
            update = self.tracker.update(result.state,result.valid_cards)
            self.observation.setText(f'{result.state.ui_state} · card confidence {result.state.detection_confidence:.0%}\n'+'\n'.join(result.state.warnings))
            if result.state.players:
                self.observation.setText(self.observation.text()+'\n'+' | '.join(f'{p["seat"]}: {p.get("state","UNKNOWN")} / stack {p.get("stack") if p.get("stack") is not None else "?"}' for p in result.state.players))
            if result.valid_cards and (update.state is None or update.state.equity_key()!=result.state.equity_key()):
                self.live.cancel()
                self.live.result = None
                self.live.probabilities.clear()
                self.live.status.setText('Waiting for three consistent frames')
            if not result.valid_cards:
                # Observed board/amounts are useful even with no visible hero
                # cards. Keep this partial frame out of equity/history tracking.
                self.live.accept_state(result.state,preserve=True)
                self.live.cancel()
                self.live.result = None
                self.live.probabilities.clear()
                if not result.state.hole_cards and result.state.board_known:
                    self.live.status.setText('Board and amounts observed. Hero cards are not visible or unreadable; equity requires two known hole cards.')
                else:
                    self.live.status.setText('Partial observation — recognized fields shown; probabilities hidden until cards are confirmed.')
            if update.changed and update.state:
                if update.new_hand:
                    if self.history.events:
                        previous = GameState.from_dict(self.history.events[-1]['state'])
                        self.repository.save(previous,mode='live',hand_id=self.history.hand_id,events=self.history.events)
                    self.history = HandHistory(update.hand_id)
                self.history.record(update.state)
                self.live.accept_state(update.state,preserve=not update.new_hand)
            elif update.state and result.valid_cards and self.tracker.count>=self.tracker.required:
                if self.live.form.base_state != update.state:
                    self.live.accept_state(update.state,preserve=True)
                elif self.live.result is None and not self.live.workers:
                    self.live.calculate(quiet=True)
        else:
            self.offline_preview.show_frame(frame,result.boxes,result.regions)
            self.offline.accept_state(result.state,preserve=False)
            self.review_status.setText(f'{result.state.ui_state} · confidence {result.state.detection_confidence:.0%}\n'+'\n'.join(result.state.warnings))

    def video_position(self,current,total):
        self.seek.setMaximum(max(0,total-1))
        if not self.seek.isSliderDown():
            self.seek.setValue(current)

    def seek_video(self):
        if self.capture and self.capture.video:
            self.capture.seek(self.seek.value())

    def load_file(self):
        path,_ = QFileDialog.getOpenFileName(self,'Open offline hand','','Poker media (*.png *.jpg *.jpeg *.bmp *.mp4 *.avi *.mov *.mkv *.json)')
        if path:
            self.load_path(Path(path))

    def load_path(self,path: Path):
        self.tabs.setCurrentIndex(2)
        if not self.stop_capture():
            return
        self.capture_target = 'offline'
        try:
            if path.suffix.lower() in ('.mp4','.avi','.mov','.mkv'):
                self.start_source('offline',video=str(path))
            elif path.suffix.lower() == '.json':
                data = json.loads(path.read_text(encoding='utf-8'))
                self.offline.accept_state(GameState.from_dict(data.get('state',data)))
                self.show_status('Loaded saved state. Confirm terminal assumptions before strategic analysis.')
            else:
                frame = cv2.imdecode(np.fromfile(path,dtype=np.uint8),cv2.IMREAD_COLOR)
                if frame is None:
                    raise ValueError('Image could not be decoded')
                self.frame_arrived(frame,self.generation)
        except (OSError,ValueError,TypeError) as exc:
            self.show_status(f'Cannot load media: {exc}')

    def demo(self):
        self.profile = LayoutProfile()
        self.vision.set_profile(self.profile)
        self.load_path(ROOT/'assets/screenshots/synthetic_demo.png')

    def rst_demo(self):
        self.profile = rst_portrait_profile()
        self.vision.set_profile(self.profile)
        self.load_path(ROOT/'assets/screenshots/rst_reference_2.png')

    def screenshot(self):
        if self.last_frame is None:
            self.show_status('No captured frame to save')
            return
        path,_ = QFileDialog.getSaveFileName(self,'Save frame','frame.png','PNG (*.png)')
        if path:
            try:
                cv2.imencode('.png',self.last_frame)[1].tofile(path)
            except OSError as exc:
                self.show_status(str(exc))

    def settings(self):
        dialog = SettingsWindow(self.profile,self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.profile = dialog.profile
            self.profile_path.write_text(self.profile.to_json(),encoding='utf-8')
            self.generation += 1
            self.stop_capture()
            self.vision.set_profile(self.profile)
            self.show_status('Layout saved. Reload the image or restart capture to apply it.')

    def add_template(self):
        path,_ = QFileDialog.getOpenFileName(self,'Choose tightly cropped card image','','Images (*.png *.jpg *.bmp)')
        if not path:
            return
        name,ok = QInputDialog.getText(self,'Card template','Card notation, e.g. Ah or Td')
        if not ok:
            return
        try:
            from poker.card import Card
            name = str(Card.parse(name))
            frame = cv2.imdecode(np.fromfile(path,dtype=np.uint8),cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError('Invalid template image')
            directory = DATA/'templates'
            directory.mkdir(parents=True,exist_ok=True)
            index = len(list(directory.glob(f'{name}_*.png')))
            cv2.imencode('.png',frame)[1].tofile(directory/f'{name}_{index}.png')
            self.vision.set_profile(self.profile)
            self.show_status(f'Added {name} template. Capture the full visible card, tightly cropped, for consistent scaling.')
        except (ValueError,OSError) as exc:
            self.show_status(str(exc))

    def save(self,panel):
        try:
            state = panel.form.state()
            self.last_saved = self.repository.save(state,panel.result,panel.analysis,panel.mode,
                self.tracker.hand_id if panel.mode=='live' else None,panel.form.corrections,
                self.history.events if panel.mode=='live' else [])
            self.show_status(f'Saved analysis #{self.last_saved} locally')
        except (ValueError,OSError) as exc:
            self.show_status(f'Cannot save: {exc}')

    def saved_hands(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Saved hands — load into offline review')
        dialog.resize(700,400)
        layout = QVBoxLayout(dialog)
        listing = QListWidget()
        records = self.repository.list()
        for identifier,created,mode,hand in records:
            listing.addItem(f'#{identifier} · {created} · {mode}')
        layout.addWidget(listing)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Open|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted and listing.currentRow() >= 0:
            identifier = records[listing.currentRow()][0]
            data = self.repository.get(identifier)
            self.tabs.setCurrentIndex(2)
            self.offline.accept_state(GameState.from_dict(data['state']))
            self.last_saved = identifier

    def export(self):
        if self.last_saved is None:
            self.show_status('Save or open an analysis before exporting')
            return
        path,_ = QFileDialog.getSaveFileName(self,'Export analysis',f'hand-{self.last_saved}.json','JSON (*.json);;CSV (*.csv)')
        if path:
            try:
                self.repository.export(self.last_saved,Path(path))
                self.show_status('Exported '+path)
            except OSError as exc:
                self.show_status(str(exc))

    def closeEvent(self,event):
        self.closing = True
        self.stop_capture()
        for panel in (self.live,self.manual,self.offline):
            panel.shutdown()
        self.vision.stop()
        self.vision.wait(1000)
        if self.vision.isRunning() or self.capture is not None or any(w.isRunning() for p in (self.live,self.manual,self.offline) for w in p.workers):
            event.ignore()
            self.show_status('Finishing background work before closing…')
            QTimer.singleShot(500,self.close)
            return
        self.repository.close()
        event.accept()

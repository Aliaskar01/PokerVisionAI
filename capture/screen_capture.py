from threading import Event, Lock
import time
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from .window_detector import window_region

class CaptureWorker(QThread):
    frame = Signal(object)
    error = Signal(str)
    position = Signal(int,int)

    def __init__(self, *, handle=None, region=None, video=None, fps=10, parent=None):
        super().__init__(parent)
        if fps not in (5,10,15,30):
            raise ValueError('FPS must be 5, 10, 15 or 30')
        if sum(x is not None for x in (handle,region,video)) != 1:
            raise ValueError('Select exactly one source')
        self.handle, self.region, self.video, self.fps = handle,region,video,fps
        self.stop_event, self.pause_event = Event(), Event()
        self.lock, self.seek_to = Lock(), None

    def stop(self):
        self.stop_event.set()

    def seek(self, frame: int):
        with self.lock:
            self.seek_to = max(0,frame)

    def run(self):
        source = None
        try:
            if self.video:
                source = cv2.VideoCapture(self.video)
                if not source.isOpened():
                    raise RuntimeError('Cannot open video')
                rate = source.get(cv2.CAP_PROP_FPS) or self.fps
                total = int(source.get(cv2.CAP_PROP_FRAME_COUNT))
            elif self.handle is None:
                import mss
                source = mss.mss()
                rate = self.fps
            else:
                from PIL import ImageGrab
                rate = self.fps
            last_error = ''
            while not self.stop_event.is_set():
                start = time.monotonic()
                with self.lock:
                    seek, self.seek_to = self.seek_to, None
                if seek is not None and self.video:
                    source.set(cv2.CAP_PROP_POS_FRAMES,seek)
                if self.pause_event.is_set() and seek is None:
                    self.stop_event.wait(.05)
                    continue
                try:
                    if self.video:
                        ok, frame = source.read()
                        if not ok:
                            self.pause_event.set()
                            continue
                        self.position.emit(int(source.get(cv2.CAP_PROP_POS_FRAMES)),total)
                    elif self.handle is not None:
                        window_region(self.handle)  # Validate existence and minimized state.
                        # Window rendering avoids reading an editor/overlay covering
                        # LetsView. Region capture still reads visible screen pixels.
                        frame=cv2.cvtColor(np.asarray(ImageGrab.grab(window=self.handle)),cv2.COLOR_RGB2BGR)
                        if frame.size==0 or frame.std()<1:
                            raise RuntimeError('Window returned a blank image. Try Region capture with the mirror visible.')
                    else:
                        frame = np.asarray(source.grab(self.region))[:,:,:3].copy()
                    self.frame.emit(frame)
                    last_error = ''
                except Exception as exc:
                    if str(exc) != last_error:
                        self.error.emit(str(exc))
                        last_error = str(exc)
                    self.stop_event.wait(.5)
                self.stop_event.wait(max(0,1/rate-(time.monotonic()-start)))
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if source is not None:
                source.release() if self.video else source.close()

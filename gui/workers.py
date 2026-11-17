from threading import Event, Lock
from PySide6.QtCore import QThread, Signal
from poker.monte_carlo import SimulationCancelled
from poker.strategy_engine import analyze
from vision.pipeline import VisionPipeline
from capture.frame_processor import FrameDeduplicator

class CalculationWorker(QThread):
    result = Signal(object,object,int)
    failure = Signal(str,int)
    progress = Signal(int,int)

    def __init__(self,calculator,state,simulations,revision,mode,options,parent=None):
        super().__init__(parent)
        self.calculator,self.state,self.simulations,self.revision,self.mode,self.options = calculator,state,simulations,revision,mode,options
        self.cancel = Event()

    def run(self):
        try:
            s = self.state
            result = self.calculator.calculate(s.hole_cards,s.community_cards,s.active_opponents,self.simulations,s.ranges,
                                              cancel=self.cancel,progress=self.progress.emit)
            analysis = None
            if self.mode != 'live':
                options = dict(self.options)
                calling_range = options.pop('calling_range','')
                if calling_range and options.get('sizes') and s.active_opponents == 1:
                    called = self.calculator.calculate(s.hole_cards,s.community_cards,1,self.simulations,(calling_range,),cancel=self.cancel)
                    options['calling_equity'] = called.equity
                analysis = analyze(s,result.equity,mode=self.mode,**options)
            if not self.cancel.is_set():
                self.result.emit(result,analysis,self.revision)
        except SimulationCancelled:
            pass
        except Exception as exc:
            self.failure.emit(str(exc),self.revision)

class VisionWorker(QThread):
    result = Signal(object,object,int)
    failure = Signal(str)

    def __init__(self,profile,parent=None):
        super().__init__(parent)
        self.profile,self.pending_profile = profile,None
        self.lock,self.wake,self.stop_event = Lock(),Event(),Event()
        self.latest = None

    def submit(self,frame,generation):
        with self.lock:
            self.latest = (frame,generation)
        self.wake.set()

    def set_profile(self,profile):
        with self.lock:
            self.pending_profile = profile
        self.wake.set()

    def stop(self):
        self.stop_event.set()
        self.wake.set()

    def run(self):
        pipeline = VisionPipeline(self.profile)
        dedup,previous,previous_generation = FrameDeduplicator(),None,None
        while not self.stop_event.is_set():
            self.wake.wait(.2)
            self.wake.clear()
            with self.lock:
                latest,self.latest = self.latest,None
                profile,self.pending_profile = self.pending_profile,None
            if profile is not None:
                pipeline = VisionPipeline(profile)
                dedup,previous = FrameDeduplicator(),None
            if latest is None:
                continue
            frame,generation = latest
            try:
                if dedup.changed(frame) or previous is None or generation != previous_generation:
                    previous = pipeline.process(frame)
                previous_generation = generation
                self.result.emit(frame,previous,generation)
            except Exception as exc:
                self.failure.emit(f'Frame skipped: {exc}')

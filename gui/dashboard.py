from PySide6.QtCore import QTimer,Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QScrollArea
from poker.equity_calculator import EquityCalculator
from poker.hand_evaluator import HandEvaluator
from .manual_calculator import ManualCalculator
from .probability_panel import ProbabilityPanel
from .review_panel import ReviewPanel
from .workers import CalculationWorker

class Dashboard(QWidget):
    save_requested = Signal()

    def __init__(self,mode):
        super().__init__()
        self.mode,self.revision,self.workers,self.result,self.analysis,self.last_state = mode,0,[],None,None,None
        self.calculator = EquityCalculator()
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        columns = QHBoxLayout(content)
        left = QWidget()
        body = QVBoxLayout(left)
        columns.addWidget(left,1)
        right = None
        if mode == 'manual':
            right = QVBoxLayout()
            columns.addLayout(right,1)
        self.summary = QLabel('Current hand · Unknown')
        self.summary.setWordWrap(True)
        body.addWidget(self.summary)
        self.form = ManualCalculator(mode)
        body.addWidget(self.form)
        buttons = QHBoxLayout()
        self.calculate_button,self.cancel_button,self.save_button = QPushButton('Calculate'),QPushButton('Cancel'),QPushButton('Save analysis')
        for button in (self.calculate_button,self.cancel_button,self.save_button):
            buttons.addWidget(button)
        body.addLayout(buttons)
        self.status = QLabel('Live observation only — no betting recommendations' if mode=='live' else 'Enter known cards. Blank numeric fields mean unknown.')
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        self.probabilities = ProbabilityPanel()
        (right or body).addWidget(self.probabilities)
        self.review = None if mode=='live' else ReviewPanel()
        if self.review:
            (right or body).addWidget(self.review)
            self.review.changed.connect(self.invalidate)
        body.addStretch()
        if right:
            right.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(600)
        self.debounce.timeout.connect(lambda:self.calculate(quiet=True))
        self.form.changed.connect(self.invalidate)
        self.calculate_button.clicked.connect(lambda:self.calculate())
        self.cancel_button.clicked.connect(self.cancel)
        self.save_button.clicked.connect(self.save_requested)

    def invalidate(self):
        self.revision += 1
        for worker in self.workers:
            worker.cancel.set()
        self.result,self.analysis = None,None
        self.probabilities.clear()
        if self.review:
            self.review.output.clear()
        self.status.setText('Inputs changed')
        self.debounce.start()

    def cancel(self):
        self.debounce.stop()
        self.revision += 1
        for worker in self.workers:
            worker.cancel.set()
        self.status.setText('Calculation canceled')

    def calculate(self,quiet=False):
        self.debounce.stop()
        try:
            state = self.form.state()
            if len(state.hole_cards)!=2:
                raise ValueError('Hole cards were not recognized. Enter both cards manually or adjust the capture layout.')
            if not state.board_known:
                raise ValueError('Board cards are unreadable. Correct the board before calculating; an unreadable board is not preflop.')
            if state.active_opponents is None or state.active_opponents < 1:
                raise ValueError('Cards recognized. Enter the number of ACTIVE opponents (1–8) to calculate equity; visible avatars do not establish activity.')
            options = self.review.options() if self.review else {}
            self.cancel()
            self.last_state = state
            strength = HandEvaluator().describe(state.hole_cards+state.community_cards) if state.community_cards else 'Preflop'
            self.summary.setText(f'{state.street} · {" ".join(state.hole_cards)} / {" ".join(state.community_cards) or "No board"} · {strength}')
            worker = CalculationWorker(self.calculator,state,int(self.form.simulations.currentText()),self.revision,self.mode,options,self)
            self.workers.append(worker)
            worker.result.connect(self._result)
            worker.failure.connect(self._error)
            worker.progress.connect(lambda done,total,w=worker:self.status.setText(f'Calculating {done:,}/{total:,}') if w.revision==self.revision else None)
            worker.finished.connect(lambda w=worker:self._finished(w))
            self.status.setText('Calculating…')
            worker.start()
        except (ValueError,TypeError) as exc:
            self.status.setText(str(exc))

    def _finished(self,worker):
        self.workers.remove(worker)
        worker.deleteLater()

    def _error(self,message,revision):
        if revision==self.revision:
            self.status.setText(message)

    def _result(self,result,analysis,revision):
        if revision != self.revision:
            return
        self.result,self.analysis = result,analysis
        self.probabilities.update_result(result)
        self.status.setText('Complete · probabilities are conditional on the entered opponent ranges')
        if self.review and analysis:
            self.review.show_analysis(analysis)

    def accept_state(self,state,preserve=False):
        try:
            previous = self.form.state().to_dict()
        except ValueError:
            previous = None
        self.form.set_state(state,preserve)
        board_label = ' '.join(state.community_cards) or ('No community cards' if state.board_known else 'Unknown board cards')
        self.summary.setText(f'{state.street} · {" ".join(state.hole_cards) or "Unknown hole cards"} / {board_label} · opponents: {state.active_opponents if state.active_opponents is not None else "Unknown"}')
        if self.form.state().to_dict() != previous:
            self.invalidate()

    def shutdown(self):
        self.cancel()
        for worker in self.workers[:]:
            worker.wait(3000)

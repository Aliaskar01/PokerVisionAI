from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QCheckBox,QLineEdit,QFormLayout,QTextEdit

class ReviewPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.terminal = QCheckBox('Assume no further betting (terminal decision model)')
        self.eligible = QCheckBox('Hero is eligible for the entire pot; no side pots')
        layout.addWidget(self.terminal)
        layout.addWidget(self.eligible)
        form = QFormLayout()
        self.sizes = QLineEdit()
        self.sizes.setPlaceholderText('Optional: 50, 100 (additional hero investment)')
        self.fold = QLineEdit()
        self.fold.setPlaceholderText('Assumed fold probability 0–1')
        self.calling = QLineEdit()
        self.calling.setPlaceholderText('Range when called, e.g. 99+,AQs+,AKo')
        for label,edit in [('Bet/raise comparison',self.sizes),('Fold probability',self.fold),('Calling range',self.calling)]:
            form.addRow(label,edit)
            edit.textChanged.connect(self.changed)
        layout.addLayout(form)
        self.terminal.toggled.connect(self.changed)
        self.eligible.toggled.connect(self.changed)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(160)
        layout.addWidget(self.output)

    def options(self):
        return dict(terminal=self.terminal.isChecked(),entire_pot_eligible=self.eligible.isChecked(),
                    sizes=tuple(float(x.strip()) for x in self.sizes.text().split(',') if x.strip()),
                    fold_probability=float(self.fold.text()) if self.fold.text().strip() else None,
                    calling_range=self.calling.text().strip())

    def show_analysis(self,analysis):
        lines = [f'Training comparison: {analysis.recommendation or "Insufficient assumptions"}',analysis.explanation,'']
        for action,details in analysis.actions.items():
            value = details.get('ev')
            lines.append(f'{action}: EV {value:+.2f}' if value is not None else f'{action}: EV unavailable')
            lines.append('  '+details.get('risk',''))
        lines.extend(['','Assumptions:']+analysis.assumptions)
        self.output.setPlainText('\n'.join(lines))

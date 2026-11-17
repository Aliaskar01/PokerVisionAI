from PySide6.QtWidgets import QWidget,QGridLayout,QLabel,QProgressBar

class ProbabilityPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        self.bars = {}
        for row,name in enumerate(('Equity','Win','Tie','Loss')):
            layout.addWidget(QLabel(name),row,0)
            bar = QProgressBar()
            bar.setRange(0,10000)
            bar.setFormat('Unknown')
            layout.addWidget(bar,row,1)
            self.bars[name.lower()] = bar
        self.details = QLabel('Enter cards and opponent assumptions')
        self.details.setWordWrap(True)
        layout.addWidget(self.details,4,0,1,2)

    def clear(self):
        for bar in self.bars.values():
            bar.setValue(0)
            bar.setFormat('Unknown')
        self.details.setText('Input changed — probabilities need recalculation')

    def update_result(self,result):
        for name,bar in self.bars.items():
            value = getattr(result,name)
            bar.setValue(round(value*10000))
            bar.setFormat(f'{value:.2%}')
        self.details.setText(f'{result.simulations:,} simulations · Monte Carlo standard error {result.standard_error:.2%}\nRanges: {", ".join(result.ranges)}\nRange uncertainty is not included in the sampling error.')

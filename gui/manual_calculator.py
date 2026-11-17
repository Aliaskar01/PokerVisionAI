from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QGridLayout,QLabel,QLineEdit,QComboBox
from poker.game_state import GameState
from poker.card import parse_cards
from poker.opponent_ranges import PROFILES,parse_range

class ManualCalculator(QWidget):
    changed = Signal()
    FIELDS = [('hole_cards','Hole cards','Ah Kh'),('community_cards','Board','Qh Jh 2c'),
              ('active_opponents','Opponents (1–8)','Unknown'),('pot','Pot incl. committed bets','Unknown'),
              ('call_amount','Amount to call','Unknown'),('hero_stack','Hero stack','Unknown'),
              ('effective_stack','Effective stack','Unknown')]

    def __init__(self,mode='manual'):
        super().__init__()
        self.mode,self.inputs,self.origins,self.overrides,self.corrections = mode,{},{},set(),[]
        self.filling = False
        self.base_state = GameState()
        layout = QGridLayout(self)
        for row,(key,label,hint) in enumerate(self.FIELDS):
            edit = QLineEdit()
            edit.setPlaceholderText(('e.g. '+hint) if mode=='manual' and key in ('hole_cards','community_cards') else
                                   'Unknown — enter cards' if key in ('hole_cards','community_cards') else hint)
            self.inputs[key] = edit
            origin = QLabel('Unknown')
            origin.setStyleSheet('color:#94a3b8;font-size:11px')
            self.origins[key] = origin
            layout.addWidget(QLabel(label),row,0)
            layout.addWidget(edit,row,1)
            layout.addWidget(origin,row,2)
            edit.textChanged.connect(lambda text,k=key:self._edited(k,text))
        self.ranges = QComboBox()
        self.ranges.setEditable(True)
        self.ranges.addItems(list(PROFILES))
        self.ranges.setToolTip('One range for all opponents, or separate ranges with |. Example: Tight | AA,AKs')
        layout.addWidget(QLabel('Opponent ranges'),7,0)
        layout.addWidget(self.ranges,7,1,1,2)
        self.ranges.currentTextChanged.connect(lambda text:self._edited('ranges',text))
        self.simulations = QComboBox()
        self.simulations.addItems(['1000','10000','50000','100000'])
        self.simulations.setCurrentText('10000')
        self.simulations.currentTextChanged.connect(self.changed)
        layout.addWidget(QLabel('Simulations'),8,0)
        layout.addWidget(self.simulations,8,1,1,2)
        if mode == 'manual':
            self.filling = True
            self.inputs['active_opponents'].setText('1')
            self.origins['active_opponents'].setText('Default assumption')
            self.filling = False

    def _edited(self,key,text):
        if self.filling:
            return
        self.overrides.add(key)
        self.corrections.append({'field':key,'value':text})
        if key in self.origins:
            self.origins[key].setText('Manual input')
        self.changed.emit()

    def state(self) -> GameState:
        values = {}
        for key,edit in self.inputs.items():
            text = edit.text().strip()
            if key in ('hole_cards','community_cards'):
                values[key] = parse_cards(text)
            elif key == 'active_opponents':
                values[key] = int(text) if text else None
            else:
                values[key] = float(text.replace(',','.')) if text else None
        ranges = tuple(x.strip() for x in self.ranges.currentText().split('|'))
        for expression in ranges:
            parse_range(expression)
        values['ranges'] = ranges
        values['sources'] = {key:label.text() for key,label in self.origins.items()}
        values['sources']['ranges'] = 'Manual input' if 'ranges' in self.overrides else 'Default assumption'
        if 'community_cards' in self.overrides:
            values['board_known'] = True
            values['visible_board_count'] = len(values['community_cards'])
        return GameState.from_dict(self.base_state.to_dict() | values)

    def set_state(self,state: GameState,preserve=False):
        self.base_state = state
        self.filling = True
        try:
            if not preserve:
                self.overrides.clear()
                self.corrections.clear()
            for key,edit in self.inputs.items():
                if preserve and key in self.overrides:
                    continue
                value = getattr(state,key)
                edit.setText(' '.join(value) if isinstance(value,tuple) else '' if value is None else f'{value:g}')
                self.origins[key].setText(state.sources.get(key,'Unknown') if value is not None and value != () else 'Unknown')
                if key == 'community_cards':
                    edit.setPlaceholderText('No community cards' if state.board_known and not value else 'Unknown — enter board cards')
                    if state.board_known and not value:
                        self.origins[key].setText(state.sources.get(key,'Manual input')+' · empty')
            if not preserve or 'ranges' not in self.overrides:
                self.ranges.setCurrentText(' | '.join(state.ranges))
        finally:
            self.filling = False

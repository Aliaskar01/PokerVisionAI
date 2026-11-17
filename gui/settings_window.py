from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPlainTextEdit,QDialogButtonBox,QMessageBox,QComboBox
from config import LayoutProfile,rst_portrait_profile

class SettingsWindow(QDialog):
    def __init__(self,profile,parent=None):
        super().__init__(parent)
        self.setWindowTitle('Detection layout — normalized coordinates')
        self.resize(760,650)
        self.profile = profile
        layout = QVBoxLayout(self)
        label = QLabel('Edit normalized x, y, w, h. When reference_size is present, vertical coordinates scale by image width so the optional bottom panel does not shift the table. Add seat_5…seat_8, stack_5…stack_8, bet_1 or call_amount as needed.')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.editor = QPlainTextEdit(profile.to_json())
        presets = QComboBox()
        presets.addItems(['Current profile','RST supplied screenshot','Generic normalized profile'])
        presets.currentIndexChanged.connect(lambda index:self.editor.setPlainText(
            [profile,rst_portrait_profile(),LayoutProfile()][index].to_json()))
        layout.addWidget(presets)
        layout.addWidget(self.editor)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate(self):
        try:
            self.profile = LayoutProfile.from_json(self.editor.toPlainText())
            self.accept()
        except (ValueError,TypeError,KeyError) as exc:
            QMessageBox.warning(self,'Invalid layout',str(exc))

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import QTimer, Qt

class PopupNotif(QWidget):
    def __init__(self, message, parent=None):
        super().__init__(parent)
                        
        self.label = QLabel(message, self)
        self.label.setAutoFillBackground(True)
        self.label.setFrameShape(QLabel.Shape.Box)
        self.label.setLineWidth(1)
        self.label.setFixedSize(300, 100)
        # Align the text in the centre of the FixedSize label
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(self.parentWidget().height() if self.parentWidget() else self.screen().availableGeometry().height())
        self.setMinimumWidth(self.parentWidget().width() if self.parentWidget() else self.screen().availableGeometry().width())
        self.setLayout(self.layout)
        
        # Timer to close the popup after 2 seconds of inactivity.
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.close)
        self.close_timer.start(2000)

    def update_popup_notif(self, message):
        self.label.setText(message)
        # Reset the timer on every update.
        self.close_timer.start(2000)
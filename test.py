from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class ResponsiveWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Responsive PyQt6 UI")
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.button = QPushButton("Responsive Button")
        layout.addWidget(self.button)

        self.setLayout(layout)

    def resizeEvent(self, event):
        # Get the current window size
        window_width = self.width()
        window_height = self.height()

        # Adjust button size based on window size
        self.button.setFixedSize(int(window_width * 0.5), int(window_height * 0.1))

        super().resizeEvent(event)

app = QApplication([])
window = ResponsiveWindow()
window.show()
app.exec()
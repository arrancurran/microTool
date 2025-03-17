import sys
from PyQt6.QtWidgets import QApplication
from interface.ui_scaffolding import uiScaffolding

app = QApplication(sys.argv)
app.setStyle("Fusion")
interface = uiScaffolding()
interface.show()
sys.exit(app.exec())
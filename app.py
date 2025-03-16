import sys
from PyQt6.QtWidgets import QApplication
from interface.interface import BaseInterface

app = QApplication(sys.argv)
interface = BaseInterface()
interface.show()
sys.exit(app.exec())
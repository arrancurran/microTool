from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

class CameraUI:
    def __init__(self, parent, cam_meta, active_camera):
        self.parent = parent
        self.active_camera = active_camera
        
        # Create and configure the camera view
        self.view = QLabel(parent)
        self.view.setMinimumSize(400, 300)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

class UIMethods(QObject):
    frame_ready = pyqtSignal()
    
    def __init__(self, window, stream_camera):
        super().__init__()
        self.window = window
        self.stream_camera = stream_camera
    
    """Update the image display with the latest frame from the stream."""
    """Convert the latest frame from the stream to a QPixmap and update the UI display."""
    def update_ui_image(self):
        np_image_data = self.stream_camera.get_latest_frame()
        if np_image_data is None:
            return
        
        height, width = np_image_data.shape
        bytes_per_line = width
        image_data = QImage(np_image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        image = QPixmap(image_data)
        
        self.window.image_container.setPixmap(image)

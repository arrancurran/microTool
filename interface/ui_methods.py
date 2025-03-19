from PyQt6.QtCore import Qt, QObject, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2

from utils import calc_img_hist

class UIMethods(QObject):
    
    def __init__(self, window, stream_camera):
        """Initialize UI methods with window and camera objects."""
        super().__init__()
        self.window = window
        self.stream_camera = stream_camera
        self.camera_control = self.stream_camera.camera_control
        
        # Setup debounce timer for exposure changes
        self.exposure_timer = QTimer()
        self.exposure_timer.setSingleShot(True)
        self.exposure_timer.timeout.connect(self._apply_exposure_change)
        self.pending_exposure = None
        
        # Connect UI elements to methods
        self.window.exposure_slider.valueChanged.connect(self.handle_exposure_change)
    
    """Get the latest frame from the stream and update the UI image display."""
    def update_ui_image(self):
        np_image_data = self.stream_camera.get_latest_frame()
        if np_image_data is None:
            return
        
        # Update the main image display
        height, width = np_image_data.shape
        bytes_per_line = width
        image_data = QImage(np_image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        image = QPixmap(image_data)
        
        image_container_size = self.window.image_container.size()
        scaled_image = image.scaled(image_container_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)        
        self.window.image_container.setPixmap(scaled_image)

        # Update the histogram 
        calc_img_hist(self.window, np_image_data)

    def handle_exposure_change(self, value):
        """Queue exposure change with debouncing."""
        # Update the exposure label immediately for responsive UI
        if hasattr(self.window, 'exposure_label'):
            self.window.exposure_label.setText(f"Exposure: {value} ms")
        
        # Store the pending value and restart the timer
        self.pending_exposure = value
        self.exposure_timer.start(20)  # 20ms debounce delay
    
    def _apply_exposure_change(self):
        """Actually apply the exposure change after debouncing."""
        if self.pending_exposure is not None:
            try:
                print(f"Setting exposure to {self.pending_exposure}")
                # Set the new exposure value using our camera control instance
                self.camera_control.call_camera_command("exposure", "set", self.pending_exposure)
                self.pending_exposure = None
            except Exception as e:
                print(f"Error setting exposure: {str(e)}")


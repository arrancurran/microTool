from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QPixmap, QImage

from instruments.xicam.cam_methods import  CameraSettings

from utils import calc_img_hist

class UIMethods(QObject):
    
    def __init__(self, window, stream_camera):
        super().__init__()
        self.window = window
        self.stream_camera = stream_camera
        # Use the camera control from stream_camera instead of creating a new one
        self.camera_settings = CameraSettings(self.stream_camera.camera_control)
        
        # Connect the exposure slider to the handler
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
        """Update camera exposure when the exposure slider value changes."""
        try:

            print(f"Setting exposure to {value}")
            # Set the new exposure value using our camera_settings instance
            self.camera_settings.call_camera_command("exposure", "set", value)
            
            # Update the exposure label if it exists
            if hasattr(self.window, 'exposure_label'):
                self.window.exposure_label.setText(f"Exposure: {value} ms")
                
        except Exception as e:
            print(f"Error setting exposure: {str(e)}")


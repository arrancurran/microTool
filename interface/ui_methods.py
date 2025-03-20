from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QImage, QPixmap
from utils import calc_img_hist
from .camera_controls.control_manager import CameraControlManager

class UIMethods(QObject):
    
    def __init__(self, window, stream_camera):
        """Initialize UI methods with window and camera objects."""
        super().__init__()
        self.window = window
        self.stream_camera = stream_camera
        self.camera_control = self.stream_camera.camera_control
        
        # Initialize camera controls
        print("Initializing camera controls in UIMethods...")  # Debug print
        self.control_manager = CameraControlManager(self.camera_control, self.window)
        self.control_manager.initialize_controls()
        
        # Verify exposure control was initialized
        exposure_control = self.control_manager.get_control('exposure')
        if exposure_control:
            print("Exposure control initialized successfully")  # Debug print
            # Test getting current exposure
            current = self.camera_control.call_camera_command("exposure", "get")
            print(f"Current exposure: {current}")  # Debug print
        else:
            print("Warning: Exposure control not initialized")  # Debug print
    
    def update_ui_image(self):
        """Get the latest frame from the stream and update the UI image display."""
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
    
    def cleanup(self):
        """Clean up resources."""
        self.control_manager.cleanup()


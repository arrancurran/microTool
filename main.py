import sys
from typing import Dict, Any
import cv2
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, 
    QWidget, QSlider, QHBoxLayout, QGridLayout
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import utils
from instruments.camera import Camera


class CameraDisplay(QLabel):
    """Widget for displaying camera feed."""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
    
    def update_image(self, image_data: Any) -> None:
        """Update the display with new image data."""
        if len(image_data.shape) == 2:
            height, width = image_data.shape
            bytes_per_line = width
            q_img = QImage(image_data.data, width, height, bytes_per_line, 
                         QImage.Format.Format_Grayscale8)
        else:
            image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
            height, width, channel = image_data.shape
            bytes_per_line = 3 * width
            q_img = QImage(image_data.data, width, height, bytes_per_line, 
                         QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(q_img)
        self.setPixmap(pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        ))


class CameraControls(QWidget):
    """Widget containing camera control elements."""
    
    def __init__(self, metadata: Dict[str, Any], parent: QWidget = None):
        super().__init__(parent)
        self.metadata = metadata
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the UI components."""
        layout = QGridLayout(self)
        
        # Histogram display
        self.hist_display = FigureCanvas(plt.figure())
        layout.addWidget(self.hist_display, 0, 1)
        
        # Exposure controls
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.exposure_slider.setStyleSheet("background-color: #FFFFFF;")
        self.exposure_slider.setRange(
            self.metadata['min_exposure'], 
            self.metadata['max_exposure']
        )
        self.exposure_slider.setValue(self.metadata['min_exposure'])
        self.exposure_slider.setTickInterval(
            (self.metadata['max_exposure'] - self.metadata['min_exposure']) // 10
        )
        self.exposure_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        
        self.exposure_label = QLabel(self)
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.update_exposure_label(self.metadata['min_exposure'])
        
        layout.addWidget(self.exposure_slider, 0, 2)
        layout.addWidget(self.exposure_label, 1, 2)
    
    def update_exposure_label(self, value: int) -> None:
        """Update the exposure label text."""
        self.exposure_label.setText(f"Exposure: {value} µs")


class XiCam(QMainWindow):
    """Main application window for the XiCam application."""
    
    def __init__(self):
        super().__init__()
        self.setup_camera()
        self.setup_ui()
        self.start_capture()
    
    def setup_camera(self) -> None:
        """Initialize the camera and get metadata."""
        self.camera = Camera()
        self.camera.start_cam()
        self.metadata = self.camera.get_cam_metadata()
        self.running = True
    
    def setup_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle('XiCam')
        self.showMaximized()
        self.setStyleSheet("background-color: #25292E;")
        
        # Main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Camera controls
        self.controls = CameraControls(self.metadata, self)
        self.controls.exposure_slider.valueChanged.connect(self.set_exposure)
        
        # Camera display
        self.display = CameraDisplay(self)
        
        # Add widgets to layout
        main_layout.addWidget(self.controls, 1)
        main_layout.addWidget(self.display, 2)
    
    def set_exposure(self, value: int) -> None:
        """Update camera exposure time."""
        self.camera.set_exposure(value)
        self.controls.update_exposure_label(value)
    
    def start_capture(self) -> None:
        """Start the image capture loop."""
        self.update_image()
    
    def update_image(self) -> None:
        """Capture and display new image frame."""
        if not self.running:
            return
            
        try:
            img_data = self.camera.capture_image()
            self.display.update_image(img_data)
            utils.calc_img_hist(self, img_data)
            QTimer.singleShot(20, self.update_image)
        except Exception as e:
            print(f"Error capturing image: {e}")
            self.running = False
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Q:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources before closing."""
        self.running = False
        self.camera.stop_cam()
        self.camera.close()
        cv2.destroyAllWindows()
        self.close()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = XiCam()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

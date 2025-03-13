import sys, cv2, matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QGridLayout, QSizePolicy,
    QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar,QWidgetAction
)
from PyQt6.QtGui import QPixmap, QImage, QAction
from PyQt6.QtCore import Qt, QTimer, QSize
# Run qta-browser from terminal to see all available icons
import qtawesome as qta
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import utils

from interface.interface import MainWindow
from instruments.camera import Camera
from interface.camera import CameraUI

# UI class that inherits from QMainWindow
class ColloidCamUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.instruments()
        self.setupUI()

    def instruments(self):
        # init cam and get cam_meta
        self.active_camera = Camera()
        self.active_camera.start_cam()
        self.cam_meta = self.active_camera.get_cam_cam_meta()
    
    def setupUI(self):

        
        self.main_window = MainWindow()  # Instantiate MainWindow
        
        # Create ROI control spinboxes

        MainWindow.roi_width.setRange(self.cam_meta['width_min'], self.cam_meta['width_max'])
        MainWindow.roi_width.setSingleStep(self.cam_meta['width_inc'])
        MainWindow.roi_width.setValue(self.cam_meta['width'])
        MainWindow.roi_width.valueChanged.connect(self.update_roi)
        
        
        MainWindow.roi_height.setRange(self.cam_meta['height_min'], self.cam_meta['height_max'])
        MainWindow.roi_height.setSingleStep(self.cam_meta['height_inc'])
        MainWindow.roi_height.setValue(self.cam_meta['height'])
        MainWindow.roi_height.valueChanged.connect(self.update_roi)
        
        
        MainWindow.roi_offset_x.setRange(0, 4000)
        MainWindow.roi_offset_x.setValue(0)
        MainWindow.roi_offset_x.valueChanged.connect(self.update_roi)
        
        
        MainWindow.roi_offset_y.setRange(0, 4000)
        MainWindow.roi_offset_y.setValue(0)
        MainWindow.roi_offset_y.valueChanged.connect(self.update_roi)
        
        
        
        
        MainWindow.exposure_slider.setRange(self.cam_meta['min_exposure'], self.cam_meta['max_exposure'])
        MainWindow.exposure_slider.setValue(self.cam_meta['min_exposure'])
        MainWindow.exposure_slider.setTickInterval((self.cam_meta['max_exposure'] - self.cam_meta['min_exposure']) // 10)
        MainWindow.exposure_slider.valueChanged.connect(self.set_exposure)
       
       
        self.set_exposure(self.cam_meta['min_exposure'])
        

        # Add play action
        play_action = QAction(qta.icon('fa5s.play'), "Play", self)
        play_action.triggered.connect(self.start_live_display)
        toolbar.addAction(play_action)

        # Add stop action
        stop_action = QAction(qta.icon('fa5s.stop'), "Stop", self)
        stop_action.triggered.connect(self.stop_live_display)
        toolbar.addAction(stop_action)

        # Add record action
        record_action = QAction(qta.icon('ei.record'), "Record", self)
        toolbar.addAction(record_action)

        # Set toolbar size
        toolbar.setFixedHeight(tollbar_height)

        self.running = False
        self.show()

    def set_exposure(self, value):
        self.active_camera.set_exposure(value)
        self.exposure_label.setText(f"Exposure: {value} µs")
        
    def update_roi(self):
        roi = {
            'width': self.roi_width.value(),
            'height': self.roi_height.value(),
            'offset_x': self.roi_offset_x.value(),
            'offset_y': self.roi_offset_y.value()
        }
        self.active_camera.update_roi(roi)

    def update_image(self):
        # if self.running:
        if not self.running:
            return
        image_data = self.active_camera.capture_image()
        height, width = image_data.shape
        bytes_per_line = width
        formated_image = QImage(image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap(formated_image)
        # Scale image to fit the view while maintaining aspect ratio
        view_size = self.view.size()
        scaled_pixmap = pixmap.scaled(
            view_size, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.view.setPixmap(scaled_pixmap)
        utils.calc_img_hist(self, image_data)
        QTimer.singleShot(20, self.update_image)
        
    def keyPressEvent(self, event):
        if  event.key() == Qt.Key.Key_Escape:  # Handle the Escape key
            self.close()  # Closes the window and triggers closeEvent

    def closeEvent(self, event):
        # Stop the camera and clean up
        if self.running:
            self.running = False
            self.active_camera.stop_cam()
            self.active_camera.close()
            cv2.destroyAllWindows()
            
        event.accept()  # Let the window close
        
    def start_live_display(self):
  
        try:
            self.update_image() # Attempt to start the camera
        except Exception as e:
            print(f"Camera start error: {e}")
            return
        self.running = True
        self.update_image()

    def stop_live_display(self):
        if self.running:
            self.running = False
            self.active_camera.stop_cam()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ColloidCamUI()
    sys.exit(app.exec())

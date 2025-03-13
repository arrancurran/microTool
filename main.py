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
        # Set initial window size
        self.resize(1200, 800)
        self.setWindowTitle('ColloidCamUI')
        self.setStyleSheet("background-color: #25292E;")
        
        # Creates the central widget
        ColloidCamUI_widget = QWidget(self)
        self.setCentralWidget(ColloidCamUI_widget)
        ColloidCamUI_layout = QHBoxLayout(ColloidCamUI_widget)
        ColloidCamUI_layout.setContentsMargins(10, 10, 10, 10)
        ColloidCamUI_layout.setSpacing(10)
        
        # Create and configure the camera view
        self.view = QLabel(self)
        self.view.setMinimumSize(400, 300)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create controls container widget with horizontal layout
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        
        # Left column for ROI controls
        roi_group = QGroupBox("Region of Interest")
        roi_layout = QFormLayout()
        
        # Create ROI control spinboxes
        self.roi_width = QSpinBox()
        self.roi_width.setRange(self.cam_meta['width_min'], self.cam_meta['width_max'])
        self.roi_width.setSingleStep(self.cam_meta['width_inc'])
        self.roi_width.setValue(self.cam_meta['width'])
        self.roi_width.valueChanged.connect(self.update_roi)
        
        self.roi_height = QSpinBox()
        self.roi_height.setRange(self.cam_meta['height_min'], self.cam_meta['height_max'])
        self.roi_height.setSingleStep(self.cam_meta['height_inc'])
        self.roi_height.setValue(self.cam_meta['height'])
        self.roi_height.valueChanged.connect(self.update_roi)
        
        self.roi_offset_x = QSpinBox()
        self.roi_offset_x.setRange(0, 4000)
        self.roi_offset_x.setValue(0)
        self.roi_offset_x.valueChanged.connect(self.update_roi)
        
        self.roi_offset_y = QSpinBox()
        self.roi_offset_y.setRange(0, 4000)
        self.roi_offset_y.setValue(0)
        self.roi_offset_y.valueChanged.connect(self.update_roi)
        
        # Add ROI controls to layout
        roi_layout.addRow("Width:", self.roi_width)
        roi_layout.addRow("Height:", self.roi_height)
        roi_layout.addRow("Offset X:", self.roi_offset_x)
        roi_layout.addRow("Offset Y:", self.roi_offset_y)
        roi_group.setLayout(roi_layout)
        
        # Right column for histogram and exposure
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        
        # Configure histogram
        self.hist_display = FigureCanvas(plt.figure())
        self.hist_display.setMinimumWidth(512)
        self.hist_display.setMaximumWidth(512)
        self.hist_display.setMinimumHeight(120)
        self.hist_display.setMaximumHeight(120)
        
        # Configure exposure slider
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setRange(self.cam_meta['min_exposure'], self.cam_meta['max_exposure'])
        self.exposure_slider.setValue(self.cam_meta['min_exposure'])
        self.exposure_slider.setTickInterval((self.cam_meta['max_exposure'] - self.cam_meta['min_exposure']) // 10)
        self.exposure_slider.valueChanged.connect(self.set_exposure)
       
        # Configure exposure label
        self.exposure_label = QLabel()
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_exposure(self.cam_meta['min_exposure'])
        
        # Add widgets to right column
        right_layout.addWidget(self.hist_display)
        right_layout.addWidget(self.exposure_slider)
        right_layout.addWidget(self.exposure_label)
        right_layout.addStretch()
        
        # Set size policies
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        roi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        right_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Add columns to controls layout
        controls_layout.addWidget(roi_group)
        controls_layout.addWidget(right_column)
        
        # Add  sections to main layout with proper ratios
        ColloidCamUI_layout.addWidget(self.view, 2)
        ColloidCamUI_layout.addWidget(controls_container, 1)
        
        # Create toolbar
        tollbar_height = 28
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(tollbar_height, tollbar_height))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

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

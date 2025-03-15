from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSizePolicy, QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar, QStatusBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSize
# Run qta-browser from terminal to see all available icons
import qtawesome as qta, matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from interface.ui_camera import ui_camera
from instruments.camera import Camera

""" 
ui_layout class sets up the main window layout. It is then called in main.py.
"""

class ui_layout(QMainWindow, ui_camera, Camera):
    def __init__(self):
        QMainWindow.__init__(self)
        ui_camera.__init__(self)
        Camera.__init__(self)
        
        self.ui_setup()
        self.ui_populate()
        self.ui_camera_setup()

    def ui_setup(self):
        
        # Set initial window size
        self.resize(1200, 800)
        self.setWindowTitle('Tweezer Camera')
        self.setStyleSheet("background-color: #25292E;")
        
        # Creates the central widget
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        MainWindow_layout.setContentsMargins(0, 0, 0, 0)
        MainWindow_layout.setSpacing(0)
        
        # Create controls container widget with horizontal layout
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        
        # Create and configure the camera image_container
        self.image_container = QLabel(self)
        self.image_container.setMinimumSize(400, 300)
        self.image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # ROI controls
        roi_group = QGroupBox("Region of Interest")
        roi_layout = QFormLayout()
        
        self.roi_width = QSpinBox()
        self.roi_height = QSpinBox()
        self.roi_offset_x = QSpinBox()
        self.roi_offset_y = QSpinBox()
        # Right column for histogram and exposure
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        
         # Add ROI controls to layout
        roi_layout.addRow("Width:", self.roi_width)
        roi_layout.addRow("Height:", self.roi_height)
        roi_layout.addRow("Offset X:", self.roi_offset_x)
        roi_layout.addRow("Offset Y:", self.roi_offset_y)
        roi_group.setLayout(roi_layout)

        # Configure histogram
        self.hist_display = FigureCanvas(plt.figure())
        self.hist_display.setMinimumWidth(512)
        self.hist_display.setMaximumWidth(512)
        self.hist_display.setMinimumHeight(120)
        self.hist_display.setMaximumHeight(120)
        
         # Configure exposure slider
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_label = QLabel()
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       
         # Add widgets to right column
        right_layout.addWidget(self.hist_display)
        right_layout.addWidget(self.exposure_slider)
        right_layout.addWidget(self.exposure_label)
        right_layout.addStretch()
        
        # Set size policies
        self.image_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        roi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        right_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Add columns to controls layout
        controls_layout.addWidget(roi_group)
        controls_layout.addWidget(right_column)
        
        # Add  sections to main layout with proper ratios
        MainWindow_layout.addWidget(self.image_container, 2)
        MainWindow_layout.addWidget(controls_container, 1)
        
        # Create toolbar
        toolbar_height = 32
        icon_size = QSize(toolbar_height, toolbar_height)*0.6
        toolbar = QToolBar("Main Toolbar")
        toolbar.setStyleSheet("background-color: #333;")  # Set toolbar style
        toolbar.setIconSize(icon_size)
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
        record_action = QAction(qta.icon('fa5.dot-circle'), "Record", self)
        record_action.triggered.connect(self.start_recording)
        toolbar.addAction(record_action)

        # Set toolbar size
        toolbar.setFixedHeight(toolbar_height)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create QLabel widgets for each piece of information
        self.camera_model_label = QLabel()
        self.camera_type_label = QLabel()
        self.roi_data_label = QLabel()
        self.framerate_label = QLabel()
        self.image_size_on_disk_label = QLabel()
        self.image_size_on_disk_bandwidth_label = QLabel()
        self.camera_model_label.setStyleSheet("padding-right: 10px;")
        self.camera_type_label.setStyleSheet("padding-right: 10px;")
        self.roi_data_label.setStyleSheet("padding-right: 10px;")
        self.framerate_label.setStyleSheet("padding-right: 10px;")
        self.image_size_on_disk_label.setStyleSheet("padding-right: 10px;")
        self.image_size_on_disk_bandwidth_label.setStyleSheet("padding-right: 10px;")
        # Add QLabel widgets to the status bar
        self.status_bar.addWidget(self.camera_model_label)
        self.status_bar.addWidget(self.camera_type_label)
        self.status_bar.addWidget(self.roi_data_label)
        self.status_bar.addWidget(self.framerate_label)
        self.status_bar.addWidget(self.image_size_on_disk_label)
        self.status_bar.addWidget(self.image_size_on_disk_bandwidth_label)
        self.update_status_bar()

    def ui_populate(self):
        ui_camera_data = ui_camera()
        
        self.roi_width.setRange(*ui_camera_data.cam_roi_width_range)
        self.roi_width.setSingleStep(self.cam_roi_width_step)
        self.roi_width.setValue(self.cam_roi_width)
        
        self.roi_height.setRange(*ui_camera_data.cam_roi_height_range)
        self.roi_height.setSingleStep(self.cam_roi_height_step)
        self.roi_height.setValue(self.cam_roi_height)
        
        self.roi_offset_x.setRange(*ui_camera_data.cam_roi_offset_x_range)
        self.roi_offset_x.setValue(self.cam_roi_offset_x)
        self.roi_offset_y.setRange(*ui_camera_data.cam_roi_offset_y_range)
        self.roi_offset_y.setValue(self.cam_roi_offset_y)
        
        self.exposure_slider.setRange(*ui_camera_data.cam_exposure_range)
        self.exposure_slider.setTickInterval(self.cam_exposure_step)
        self.exposure_slider.setValue(self.cam_exposure)
        

    def update_status_bar(self):
        camera_meta = self.get_cam_meta()
        # Update each QLabel with the respective information
        self.camera_model_label.setText(f"{camera_meta['device_name']}")
        self.camera_type_label.setText(f"{camera_meta['device_type']}")
        self.roi_data_label.setText(f"{camera_meta['width']}x{camera_meta['height']}")
        self.framerate_label.setText(f"@ {int(camera_meta['framerate'])} Hz")
        image_size_on_disk = camera_meta['width']*camera_meta['height']/1024/1024
        self.image_size_on_disk_label.setText(f"{image_size_on_disk:.2f} MB")
        image_size_on_disk_bandwidth = image_size_on_disk*camera_meta['framerate']
        self.image_size_on_disk_bandwidth_label.setText(f"{image_size_on_disk_bandwidth:.2f} MB/s")
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSizePolicy,
    QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSize
# Run qta-browser from terminal to see all available icons
import qtawesome as qta, matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

""" ui_layout class sets up the main window layout. It is then called in main.py."""

class ui_layout(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setup_ui()

    def setup_ui(self):
        # Set initial window size
        self.resize(1200, 800)
        self.setWindowTitle('ColloidCam')
        self.setStyleSheet("background-color: #25292E;")
        
        # Creates the central widget
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        MainWindow_layout.setContentsMargins(10, 10, 10, 10)
        MainWindow_layout.setSpacing(10)
        
        # Create controls container widget with horizontal layout
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        
        # Create and configure the camera view
        self.view = QLabel(self)
        self.view.setMinimumSize(400, 300)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        roi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        right_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Add columns to controls layout
        controls_layout.addWidget(roi_group)
        controls_layout.addWidget(right_column)
        
        # Add  sections to main layout with proper ratios
        MainWindow_layout.addWidget(self.view, 2)
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

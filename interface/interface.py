from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QGridLayout, QSizePolicy,
    QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar,QWidgetAction
)
from PyQt6.QtGui import QPixmap, QImage, QAction
from PyQt6.QtCore import Qt, QTimer, QSize
# Run qta-browser from terminal to see all available icons
import qtawesome as qta, matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui_layout()

    def ui_layout(self):
        # Set initial window size
        self.resize(1200, 800)
        self.setWindowTitle('MainWindow')
        self.setStyleSheet("background-color: #25292E;")
        
        # Creates the central widget
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        MainWindow_layout.setContentsMargins(10, 10, 10, 10)
        MainWindow_layout.setSpacing(10)
        
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
        self.roi_height = QSpinBox()
        self.roi_offset_x = QSpinBox()
        self.roi_offset_y = QSpinBox()
        
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
        
         # Configure exposure label
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
        ColloidCamUI_layout.addWidget(self.view, 2)
        ColloidCamUI_layout.addWidget(controls_container, 1)
        
        # Create toolbar
        tollbar_height = 28
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(tollbar_height, tollbar_height))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
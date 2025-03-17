from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSizePolicy, QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar, QStatusBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSize
# Run qta-browser from terminal to see all available icons
import qtawesome as qta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import json, os

""" 
ui_layout class sets up the main window layout. It is then called in main.py.
"""

class uiScaffolding(QMainWindow):
    """
    Base interface class that contains all UI elements without hardware dependencies.
    """
    def __init__(self):
        super().__init__()
        self.ui_settings = self.load_settings()
        self.ui_scaffold()

    def load_settings(self):
        """Load settings from ui_settings.json"""
        settings_path = 'ui_settings.json'
        with open(settings_path, 'r') as f:
            return json.load(f)

    def ui_scaffold(self):
        """Set up the main window"""
        window_settings = self.ui_settings['window']
        self.resize(window_settings['initial_width'], window_settings['initial_height'])
        self.setWindowTitle(window_settings['title'])
        # self.setStyleSheet(f"background-color: {window_settings['background_color']};")
        
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        
        layout_settings = self.ui_settings['window']['margins']
        MainWindow_layout.setContentsMargins(
            layout_settings['left'],
            layout_settings['top'],
            layout_settings['right'],
            layout_settings['bottom']
        )
        MainWindow_layout.setSpacing( self.ui_settings['window']['spacing'])
        
        """Create controls container with horizontal layout"""
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        margins = self.ui_settings['container']['margins']
        controls_layout.setContentsMargins(
            margins['left'],
            margins['top'], 
            margins['right'],
            margins['bottom']
        )
        controls_layout.setSpacing(self.ui_settings['container']['spacing'])
        
        """Create and configure the camera image_container"""
        self.image_container = QLabel(self)
        image_settings = self.ui_settings['image_display']
        self.image_container.setMinimumSize(image_settings['min_width'], image_settings['min_height'])
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
        self.hist_figure = plt.figure()
        self.hist_display = FigureCanvas(self.hist_figure)
        self.hist_display.setFixedSize(512, 120)
        
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
        
        # Add sections to main layout with proper ratios
        MainWindow_layout.addWidget(self.image_container, 2)
        MainWindow_layout.addWidget(controls_container, 1)
        
        # Create toolbar
        toolbar_height = self.ui_settings['toolbar']['height']
        icon_size = QSize(self.ui_settings['toolbar']['icon_size'], self.ui_settings['toolbar']['icon_size'])
        # background_color = self.ui_settings['toolbar']['background_color']
        
        toolbar = QToolBar("Main Toolbar")
        toolbar.setFixedHeight(toolbar_height)
        # toolbar.setStyleSheet(f"background-color: {background_color};")
        toolbar.setIconSize(icon_size)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        # Add actions to toolbar
        for icon_name, icon_path in self.ui_settings['toolbar']['icons'].items():
            action = QAction(qta.icon(icon_path), icon_name, self)
            action.triggered.connect(getattr(self, f"{icon_name}"))
            toolbar.addAction(action)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
       
        # Create and add QLabel widgets for each piece of information
        for label_name, label_text in self.ui_settings['status_bar']['labels'].items():
            label = QLabel()
            setattr(self, f"{label_name}_label", label)
            self.status_bar.addWidget(label)
            label.setText(label_text)

    def start_stream(self):
        """Override this method in derived classes to implement camera-specific live display"""
        pass

    def stop_stream(self):
        """Override this method in derived classes to implement camera-specific stop display"""
        pass

    def start_recording(self):
        """Override this method in derived classes to implement camera-specific recording"""
        pass
    
    def snapshot(self):
        """Override this method in derived classes to implement camera-specific recording"""
        pass


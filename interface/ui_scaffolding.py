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
        
        self.settings = self.load_settings()
        
        self.ui_scaffold()

    def load_settings(self):
        """Load settings from ui_settings.json"""
        settings_path = 'ui_settings.json'
        with open(settings_path, 'r') as f:
            return json.load(f)

    def ui_scaffold(self):
        """Set up the main window"""
        window_settings = self.settings['window']
        self.resize(window_settings['initial_width'], window_settings['initial_height'])
        self.setWindowTitle(window_settings['title'])
        self.setStyleSheet(f"background-color: {window_settings['background_color']};")
        
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        
        layout_settings = self.settings['window']['margins']
        MainWindow_layout.setContentsMargins(
            layout_settings['left'],
            layout_settings['top'],
            layout_settings['right'],
            layout_settings['bottom']
        )
        MainWindow_layout.setSpacing( self.settings['window']['spacing'])
        
        """Create controls container with horizontal layout"""
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        margins = self.settings['container']['margins']
        controls_layout.setContentsMargins(
            margins['left'],
            margins['top'], 
            margins['right'],
            margins['bottom']
        )
        controls_layout.setSpacing(self.settings['container']['spacing'])
        
        """Create and configure the camera image_container"""
        self.image_container = QLabel(self)
        image_settings = self.settings['image_display']
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
        self.hist_ax = self.hist_figure.add_subplot(111)
        self.hist_ax.set_title('Image Histogram')
        self.hist_ax.set_xlabel('Intensity')
        self.hist_ax.set_ylabel('Count')
        
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
        
        # Set styles for labels
        for label in [self.camera_model_label, self.camera_type_label, 
                     self.roi_data_label, self.framerate_label,
                     self.image_size_on_disk_label, self.image_size_on_disk_bandwidth_label]:
            label.setStyleSheet("padding-right: 10px;")
        
        # Add QLabel widgets to the status bar
        self.status_bar.addWidget(self.camera_model_label)
        self.status_bar.addWidget(self.camera_type_label)
        self.status_bar.addWidget(self.roi_data_label)
        self.status_bar.addWidget(self.framerate_label)
        self.status_bar.addWidget(self.image_size_on_disk_label)
        self.status_bar.addWidget(self.image_size_on_disk_bandwidth_label)

    # def ui_populate(self):
    #     # Set ROI controls from settings
    #     roi_settings = self.settings['roi']
        
    #     # Width settings
    #     self.roi_width.setRange(roi_settings['width']['min'], roi_settings['width']['max'])
    #     self.roi_width.setSingleStep(roi_settings['width']['step'])
    #     self.roi_width.setValue(roi_settings['width']['default'])
        
    #     # Height settings
    #     self.roi_height.setRange(roi_settings['height']['min'], roi_settings['height']['max'])
    #     self.roi_height.setSingleStep(roi_settings['height']['step'])
    #     self.roi_height.setValue(roi_settings['height']['default'])
        
    #     # Offset X settings
    #     self.roi_offset_x.setRange(roi_settings['offset_x']['min'], roi_settings['offset_x']['max'])
    #     self.roi_offset_x.setSingleStep(roi_settings['offset_x']['step'])
    #     self.roi_offset_x.setValue(roi_settings['offset_x']['default'])
        
    #     # Offset Y settings
    #     self.roi_offset_y.setRange(roi_settings['offset_y']['min'], roi_settings['offset_y']['max'])
    #     self.roi_offset_y.setSingleStep(roi_settings['offset_y']['step'])
    #     self.roi_offset_y.setValue(roi_settings['offset_y']['default'])
        
    #     # Set exposure slider range and default value
    #     self.exposure_slider.setRange(0, 10000)
    #     self.exposure_slider.setValue(1000)
        
    #     # Update status bar with default values
    #     self.update_status_bar()

    def update_status_bar(self):
        # Update status bar with default values
        self.camera_model_label.setText("No Camera")
        self.camera_type_label.setText("Not Connected")
        self.roi_data_label.setText(f"{self.roi_width.value()}x{self.roi_height.value()}")
        self.framerate_label.setText("@ 0 Hz")
        self.image_size_on_disk_label.setText("0.00 MB")
        self.image_size_on_disk_bandwidth_label.setText("0.00 MB/s")

    def start_live_display(self):
        """Override this method in derived classes to implement camera-specific live display"""
        pass

    def stop_live_display(self):
        """Override this method in derived classes to implement camera-specific stop display"""
        pass

    def start_recording(self):
        """Override this method in derived classes to implement camera-specific recording"""
        pass

    def update_histogram(self, data, bins=256):
        """
        Update the histogram display with new data.
        
        Args:
            data (numpy.ndarray): The image data to create histogram from
            bins (int): Number of bins for the histogram
        """
        self.hist_ax.clear()
        self.hist_ax.hist(data.ravel(), bins=bins, range=(0, 256))
        self.hist_ax.set_title('Image Histogram')
        self.hist_ax.set_xlabel('Intensity')
        self.hist_ax.set_ylabel('Count')
        self.hist_display.draw()

class ui_layout(uiScaffolding):
    """
    Camera-specific interface class that inherits from uiScaffolding and adds camera functionality.
    """
    def __init__(self):
        uiScaffolding.__init__(self)
        self.ui_camera_setup()

    def ui_camera_setup(self):
        """Setup camera-specific UI elements and connections"""
        pass
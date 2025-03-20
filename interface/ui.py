from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSizePolicy, QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar, QStatusBar, QStyle
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
# Run qta-browser from terminal to see all available icons
import qtawesome as qta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import json, os

""" 
ui_layout class sets up the main window layout. It is then called in main.py.
"""

class ui(QMainWindow):
    """
    Base interface class that contains all UI elements without hardware dependencies.
    """
    def __init__(self):
        super().__init__()
        self.ui_scaffolding = self.load_json('ui_scaffolding.json')
        self.build_ui()
        # self.apply_styles()  # Apply styling after UI is built

    def load_json(self, file_path):
        """Load settings from ui_settings.json"""
        with open(os.path.join('interface', file_path), 'r') as f:
            return json.load(f)

    def apply_styles(self):
        with open(os.path.join('interface', "style.css"), "r") as f:
            self.setStyleSheet(f.read())
    
    def build_ui(self):
        """Main Window"""
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        
        """Controls Container"""
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)

        """Camera Image Container"""
        self.image_container = QLabel(self)
        image_scaffolding = self.ui_scaffolding['image_display']
        self.image_container.setMinimumSize(image_scaffolding['min_width'], image_scaffolding['min_height'])
        self.image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        """ROI Group Box"""
        roi_group = QGroupBox("Region of Interest")
        roi_layout = QFormLayout()
        
        self.roi_width = QSpinBox()
        self.roi_height = QSpinBox()
        self.roi_offset_x = QSpinBox()
        self.roi_offset_y = QSpinBox()
        
        # Set fixed width for ROI inputs
        roi_input_width = self.ui_scaffolding['roi']['input_width']
        for spinbox in [self.roi_width, self.roi_height, self.roi_offset_x, self.roi_offset_y]:
            spinbox.setFixedWidth(roi_input_width)
        
        """Right Column"""
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        
        """Add ROI Controls to Layout"""
        roi_layout.addRow("Width:", self.roi_width)
        roi_layout.addRow("Height:", self.roi_height)
        roi_layout.addRow("Offset X:", self.roi_offset_x)
        roi_layout.addRow("Offset Y:", self.roi_offset_y)
        roi_group.setLayout(roi_layout)

        """Histogram"""
        self.hist_figure = plt.figure()
        self.hist_display = FigureCanvas(self.hist_figure)
        self.hist_display.setFixedSize(512, 120)
        
        """Exposure Slider"""
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_label = QLabel()
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        """Add Widgets to Right Column"""
        right_layout.addWidget(self.hist_display)
        right_layout.addWidget(self.exposure_slider)
        right_layout.addWidget(self.exposure_label)
        right_layout.addStretch()
        
        """Set Size Policies"""
        self.image_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        roi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        right_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        """Add Columns to Controls Layout"""
        controls_layout.addWidget(roi_group)
        controls_layout.addWidget(right_column)
        
        """Add Sections to Main Layout with Proper Ratios"""
        MainWindow_layout.addWidget(self.image_container, 2)
        MainWindow_layout.addWidget(controls_container, 1)
        
        """Toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        """Status Bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
       
        """Create and add QLabel widgets for each piece of information"""
        for label_name, label_text in self.ui_scaffolding['status_bar']['labels'].items():
            label = QLabel()
            setattr(self, f"{label_name}_label", label)
            self.status_bar.addWidget(label)
            label.setText(label_text)

        # """Add Actions to Toolbar"""
        # self.start_stream = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Start Stream", self)
        # self.stop_stream = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop), "Stop Stream", self)
        # self.snapshot = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Take Snapshot", self)
        # self.start_recording = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaRecord), "Record", self)
        
        # toolbar.addAction(self.start_stream)
        # toolbar.addAction(self.stop_stream)
        # toolbar.addAction(self.snapshot)
        # toolbar.addAction(self.start_recording)




        for action, icon_path in self.ui_scaffolding['toolbar']['icons'].items():
            action_obj = QAction(qta.icon(icon_path), action, self)
            toolbar.addAction(action_obj)
            setattr(self, action, action_obj)
        # self.start_stream = QAction(qta.icon("fa5s.play"), "Start Stream", self)
        # self.stop_stream = QAction(qta.icon("fa5s.stop"), "Stop Stream", self)

        # toolbar.addAction(self.start_stream)
        # toolbar.addAction(self.stop_stream)

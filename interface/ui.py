
import json, os
import pyqtgraph as pg  
import qtawesome as qta

from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSizePolicy, QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar, QStatusBar, QPushButton
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from .ui_img_disp import DispMouseHandler
from utils.img_hist_disp import ImgHistDisplay

# Inherit from QMainWindow so ui is our main window
class ui(QMainWindow):

    def __init__(self):

        super().__init__()
        self.ui_scaffolding = self.load_ui_scaffolding('ui_scaffolding.json')
        ### TOOLBAR ###
        self.setup_toolbar()

        ### IMAGE CONTAINER ###
        # image_container = self.create_image_container()
        
        ### HISTOGRAM ### 
        self.setup_histogram()
        
        ### EXPOSURE SLIDER ###
        self.setup_exposure_slider()
        
        ### STATUS BAR ###
        self.setup_status_bar()
        
        ### Build the rest of the UI ###
        self.build_ui()
        
        # self.apply_styles()  # Apply styling after UI is built

    # def apply_styles(self):
    #     with open(os.path.join('interface', "style.css"), "r") as f:
    #         self.setStyleSheet(f.read())
    
    def load_ui_scaffolding(self, file_path):
        with open(os.path.join('interface', file_path), 'r') as f:
            return json.load(f)
    
    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        # Add actions
        for action_name, action_data in self.ui_scaffolding['toolbar']['icons'].items():
            action_obj = QAction(qta.icon(action_data['icon']), action_name, self)
            action_obj.setToolTip(action_data['tooltip'])
            toolbar.addAction(action_obj)
            setattr(self, action_data['cmd'], action_obj)
    
    def create_image_container(self):
        image_container = DispMouseHandler(self)
        image_scaffolding = self.ui_scaffolding['image_display']
        image_container.setMinimumSize(image_scaffolding['min_width'], image_scaffolding['min_height'])
        image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return image_container
    
    def create_roi_controls(self):
        roi_group = QGroupBox("Region of Interest")
        roi_layout = QVBoxLayout()
        
        roi_form_layout = QFormLayout()
        self.roi_width = QSpinBox()
        self.roi_height = QSpinBox()
        self.roi_offset_x = QSpinBox()
        self.roi_offset_y = QSpinBox()
        
        roi_input_width = self.ui_scaffolding['roi']['input_width']
        for spinbox in [self.roi_width, self.roi_height, self.roi_offset_x, self.roi_offset_y]:
            spinbox.setFixedWidth(roi_input_width)
        
        roi_form_layout.addRow("Width:", self.roi_width)
        roi_form_layout.addRow("Height:", self.roi_height)
        roi_form_layout.addRow("Offset X:", self.roi_offset_x)
        roi_form_layout.addRow("Offset Y:", self.roi_offset_y)
        roi_layout.addLayout(roi_form_layout)
        
        # Add buttons below ROI controls
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.apply_roi_button = QPushButton("Apply ROI")
        self.apply_roi_button.setFixedWidth(200)
        button_layout.addWidget(self.apply_roi_button)
        
        self.reset_roi_button = QPushButton("Reset ROI")
        self.reset_roi_button.setFixedWidth(200)
        button_layout.addWidget(self.reset_roi_button)
        
        roi_layout.addWidget(button_container)
        roi_group.setLayout(roi_layout)
        roi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        return roi_group
    
    def setup_histogram(self):
        self.hist_display = pg.PlotWidget()
        self.hist_display.setFixedSize(512, 120)
        self.histogram_plot = ImgHistDisplay(self.hist_display)
    
    def setup_exposure_slider(self):
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_label = QLabel()
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def create_right_column(self):
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)

        right_layout.addWidget(self.hist_display)
        right_layout.addWidget(self.exposure_slider)
        right_layout.addWidget(self.exposure_label)
        right_layout.addStretch()

        right_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        return right_column
            
    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        for label_name, label_text in self.ui_scaffolding['status_bar']['labels'].items():
            label = QLabel()
            setattr(self, f"{label_name}_label", label)
            self.status_bar.addWidget(label)
            label.setText(label_text)
    
    def build_ui(self):
        # Using a QWidget as the central widget inside QMainWindow helps separate the layout 
        # and content of the main window from the QMainWindow.
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget_layout = QHBoxLayout(central_widget)

         ### IMAGE CONTAINER ###
        self.image_container = self.create_image_container()
        
        ### CONTROLS CONTAINER ###
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        
        
        # Add ROI controls and right column to controls layout
        roi_group = self.create_roi_controls()
        right_column = self.create_right_column()
        controls_layout.addWidget(roi_group)
        controls_layout.addWidget(right_column)
       
        
        # Add Sections to Main Layout with Proper Ratios
        central_widget_layout.addWidget(self.image_container, 2)
        central_widget_layout.addWidget(controls_container, 1)
        
        self.setWindowTitle(f"{self.ui_scaffolding['app']['name']} - {self.ui_scaffolding['app']['version']}")
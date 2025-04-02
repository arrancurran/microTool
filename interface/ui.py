
import json, os
import pyqtgraph as pg  
import qtawesome as qta

from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSpinBox, QVBoxLayout, QToolBar, QStatusBar, QPushButton, QGridLayout
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
        
        # self.apply_styles()

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
        image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return image_container
    
    def setup_roi(self):
        roi_group_widget = QWidget()
        roi_grid_layout = QGridLayout(roi_group_widget)
        roi_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        spinbox_width = self.ui_scaffolding['spinbox']['width']
        
        for count, (key, value)  in enumerate(self.ui_scaffolding['roi'].items()):
            roi_spinbox = QSpinBox()
            roi_label = QLabel(value.get("label", "No Label"))

            roi_container = QWidget()
            roi_layout = QHBoxLayout(roi_container)
            roi_layout.setContentsMargins(0, 0, 0, 0)
            
            roi_layout.addWidget(roi_label)
            roi_layout.addWidget(roi_spinbox)
            
            roi_spinbox.setFixedWidth(spinbox_width)
            roi_spinbox.setAlignment(Qt.AlignmentFlag.AlignTop)
            roi_spinbox.setToolTip(value.get("tooltip", "No Tooltip"))
            
            setattr(self, f"roi_{key}", roi_spinbox)
            
            roi_grid_index = (count // 2, count % 2)
            
            roi_grid_layout.addWidget(roi_container, roi_grid_index[0], roi_grid_index[1])
            roi_grid_layout.setAlignment(roi_container, Qt.AlignmentFlag.AlignRight)

        # Add buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        self.apply_roi_button = QPushButton("Apply ROI")
        button_layout.addWidget(self.apply_roi_button)
        
        self.reset_roi_button = QPushButton("Reset ROI")
        button_layout.addWidget(self.reset_roi_button)
        
        roi_grid_layout.addWidget(button_container, 2, 0, 1, 2)
        
        roi_group_widget.setLayout(roi_grid_layout)

        return roi_group_widget
    
    def setup_histogram(self):
        self.hist_display = pg.PlotWidget()
        self.hist_display.setFixedHeight(120)
        self.histogram_plot = ImgHistDisplay(self.hist_display)
    
    def setup_exposure_slider(self):
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setTickInterval(5000)
        self.exposure_slider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.exposure_label = QLabel()
    
    def create_controls_narrow(self):
        controls_narrow = QWidget()
        controls_narrow_layout = QVBoxLayout(controls_narrow)
        
        controls_narrow_layout.addWidget(self.setup_roi())
        # Add more controls here as needed
        return controls_narrow
    
    def create_controls_wide(self):
        controls_wide = QWidget()
        controls_wide_layout = QVBoxLayout(controls_wide)

        controls_wide_layout.addWidget(self.hist_display)
        controls_wide_layout.addWidget(self.exposure_slider)
        controls_wide_layout.addWidget(self.exposure_label)

        return controls_wide
            
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

         ### IMAGE  ###
        self.image_container = self.create_image_container()

        ### CONTROLS  ###
        controls_narrow = self.create_controls_narrow()
        controls_wide = self.create_controls_wide()

        # Add Sections to Main Layout
        central_widget_layout.addWidget(self.image_container)
        central_widget_layout.addWidget(controls_narrow)
        central_widget_layout.addWidget(controls_wide)
        
        central_widget_layout.setStretch(0, 5) # Set Image to 50%
        central_widget_layout.setStretch(1, 2) # Set narrow to 20%
        central_widget_layout.setStretch(2, 3) # Set wide to 30%
        
        self.setWindowTitle(f"{self.ui_scaffolding['app']['name']} - {self.ui_scaffolding['app']['version']}")
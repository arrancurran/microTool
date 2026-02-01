
# Create all the UI elements and set their layout and properties
import json, os
import pyqtgraph as pg  
import qtawesome as qta

from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSpinBox, QVBoxLayout, QToolBar, QStatusBar, QPushButton, QGridLayout, QLineEdit, QFileDialog, QGroupBox, QComboBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from .ui_img_disp import DispMouseHandler
from utils.img_hist_disp import ImgHistDisplay

# Inherit from QMainWindow so ui is our main window
class AppUI(QMainWindow):

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
        # Group box to visually contain ROI controls
        roi_group_widget = QGroupBox("Region of Interest Settings")
        roi_grid_layout = QGridLayout()
        roi_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        spinbox_width = self.ui_scaffolding['spinbox']['width']
        
        for count, (key, value) in enumerate(self.ui_scaffolding['roi'].items()):
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

    def setup_experiment_controls(self):
        """Create controls for experiment directory, name, mode and frame rate.

        Displayed inside a titled group box "Acquisition Settings".
        """
        group = QGroupBox("Acquisition Settings")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)

        # Acquisition mode row
        mode_row = QWidget()
        mode_layout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        mode_label = QLabel("Mode:")
        self.acquisition_mode_combo = QComboBox()
        self.acquisition_mode_combo.addItems([
            "Free run (max speed)",
            "Frame rate mode",
        ])

        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.acquisition_mode_combo)

        # Directory row
        dir_row = QWidget()
        dir_layout = QHBoxLayout(dir_row)
        dir_layout.setContentsMargins(0, 0, 0, 0)

        dir_label = QLabel("Directory:")
        self.experiment_dir_edit = QLineEdit()
        browse_button = QPushButton("Browse")

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.experiment_dir_edit)
        dir_layout.addWidget(browse_button)

        # Experiment name row
        name_row = QWidget()
        name_layout = QHBoxLayout(name_row)
        name_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel("Experiment name:")
        self.experiment_name_edit = QLineEdit()

        name_layout.addWidget(name_label)
        name_layout.addWidget(self.experiment_name_edit)

        # Experiment frame rate row
        fr_row = QWidget()
        fr_layout = QHBoxLayout(fr_row)
        fr_layout.setContentsMargins(0, 0, 0, 0)

        fr_label = QLabel("Frame rate (Hz):")
        self.experiment_framerate_edit = QLineEdit()

        fr_layout.addWidget(fr_label)
        fr_layout.addWidget(self.experiment_framerate_edit)

        # Experiment frames row (how many frames to acquire)
        frames_row = QWidget()
        frames_layout = QHBoxLayout(frames_row)
        frames_layout.setContentsMargins(0, 0, 0, 0)

        frames_label = QLabel("Frames to acquire:")
        self.experiment_frames_edit = QLineEdit()
        self.experiment_frames_edit.setText("100")

        frames_layout.addWidget(frames_label)
        frames_layout.addWidget(self.experiment_frames_edit)

        layout.addWidget(mode_row)
        layout.addWidget(dir_row)
        layout.addWidget(name_row)
        layout.addWidget(fr_row)
        layout.addWidget(frames_row)

        # Connect browse button to QFileDialog
        def _browse_dir():
            directory = QFileDialog.getExistingDirectory(self, "Select Experiment Directory")
            if directory:
                self.experiment_dir_edit.setText(directory)

        browse_button.clicked.connect(_browse_dir)

        return group
    
    def setup_exposure_slider(self):
        # Container so slider and label can sit side by side
        self.exposure_container = QWidget()
        exposure_layout = QHBoxLayout(self.exposure_container)
        exposure_layout.setContentsMargins(0, 0, 0, 0)

        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setTickInterval(5000)
        self.exposure_slider.setTickPosition(QSlider.TickPosition.TicksAbove)

        self.exposure_label = QLabel()
        # Keep the value close to the slider, aligned right
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        exposure_layout.addWidget(self.exposure_slider)
        exposure_layout.addWidget(self.exposure_label)
    
    def create_controls_narrow(self):
        controls_narrow = QWidget()
        controls_narrow_layout = QVBoxLayout(controls_narrow)
        
        controls_narrow_layout.addWidget(self.setup_roi())
        # Experiment configuration controls (directory + name)
        controls_narrow_layout.addWidget(self.setup_experiment_controls())
        return controls_narrow
    
    def create_controls_wide(self):
        controls_wide = QWidget()
        controls_wide_layout = QVBoxLayout(controls_wide)
        # Ensure controls stack from the top (no vertical centering)
        controls_wide_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        controls_wide_layout.addWidget(self.hist_display)
        # Add combined exposure slider + label widget
        controls_wide_layout.addWidget(self.exposure_container)

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
        # Ensure side control columns are aligned to the top
        central_widget_layout.setAlignment(controls_narrow, Qt.AlignmentFlag.AlignTop)
        central_widget_layout.setAlignment(controls_wide, Qt.AlignmentFlag.AlignTop)
        
        central_widget_layout.setStretch(0, 5) # Set Image to 50%
        central_widget_layout.setStretch(1, 2) # Set narrow to 20%
        central_widget_layout.setStretch(2, 3) # Set wide to 30%
        
        self.setWindowTitle(f"{self.ui_scaffolding['app']['name']} - {self.ui_scaffolding['app']['version']}")
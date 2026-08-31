
# Create all the UI elements and set their layout and properties
import json, os, logging
import math
import pyqtgraph as pg  
import qtawesome as qta

from PyQt6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QSlider,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QToolBar,
    QStatusBar,
    QPushButton,
    QGridLayout,
    QLineEdit,
    QFileDialog,
    QGroupBox,
    QComboBox,
    QDoubleSpinBox,
    QTabWidget,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer

from .ui_img_disp import DispMouseHandler
from utils.img_hist_disp import ImgHistDisplay
from instruments.SLM.udp_holo import (
    get_coordinate_scales,
    send_traps,
    set_coordinate_scales,
)

logger = logging.getLogger(__name__)

CAMERA_PIXELS_PER_UM = 12.18

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

    # ---- Optical trap helpers -------------------------------------------------

    def _current_optical_trap_index(self):
        if not hasattr(self, "optical_traps"):
            return -1
        return self.optical_trap_selector.currentIndex()

    def _apply_optical_trap_to_widgets(self, trap):
        """Populate parameter widgets from a trap dict."""

        if trap is None:
            return

        # Guard against missing keys; fall back to widget's current value
        for attr_name, param_key in self._optical_trap_param_map.items():
            spin = getattr(self, attr_name)
            value = trap.get(param_key, spin.value())
            spin.blockSignals(True)
            spin.setValue(float(value))
            spin.blockSignals(False)

    def _on_optical_trap_param_changed(self, param_key, value):
        """Update the currently-selected trap dict when a parameter changes."""

        idx = self._current_optical_trap_index()
        logger.debug(f"Spin changed: idx={idx}, param={param_key}, value={value}")
        if idx < 0 or idx >= len(self.optical_traps):
            logger.debug("Ignoring change: no valid trap selected.")
            return
        self.optical_traps[idx][param_key] = float(value)

        # Push updated trap configuration to the SLM.
        self._send_optical_traps_to_slm()

    def _on_optical_trap_changed(self, index):
        """Handle switching between spots in the selector."""

        if not hasattr(self, "optical_traps") or index < 0 or index >= len(self.optical_traps):
            return
        trap = self.optical_traps[index]
        self._apply_optical_trap_to_widgets(trap)

    def _add_optical_trap(self):
        """Add a new spot with default parameters and select it."""

        if not hasattr(self, "optical_traps"):
            self.optical_traps = []

        default_trap = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "intensity": 1.0,
            "vortex": 0.0,
            "phase": 0.0,
        }
        self.optical_traps.append(default_trap)

        spot_index = len(self.optical_traps)
        self.optical_trap_selector.addItem(f"Spot {spot_index}")
        self.optical_trap_selector.setCurrentIndex(spot_index - 1)
        self._apply_optical_trap_to_widgets(default_trap)

        # Notify SLM of the new spot configuration.
        self._send_optical_traps_to_slm()

    def _remove_optical_trap(self):
        """Remove the currently-selected spot (keeping at least one)."""

        if not hasattr(self, "optical_traps") or len(self.optical_traps) <= 1:
            # Always keep at least one spot to avoid empty UI state
            return

        idx = self._current_optical_trap_index()
        if idx < 0 or idx >= len(self.optical_traps):
            return

        del self.optical_traps[idx]
        self.optical_trap_selector.removeItem(idx)

        # Re-label remaining spots as Spot 1, Spot 2, ...
        for i in range(self.optical_trap_selector.count()):
            self.optical_trap_selector.setItemText(i, f"Spot {i + 1}")

        # Ensure a valid selection remains
        if self.optical_trap_selector.count() > 0:
            new_index = min(idx, self.optical_trap_selector.count() - 1)
            self.optical_trap_selector.setCurrentIndex(new_index)

        # Notify SLM after removing a spot.
        self._send_optical_traps_to_slm()

    def _replace_optical_traps(self, traps):
        """Replace every spot, refresh the selector, and send one update."""

        if not traps:
            return

        self.optical_traps = traps

        signals_were_blocked = self.optical_trap_selector.blockSignals(True)
        try:
            self.optical_trap_selector.clear()
            self.optical_trap_selector.addItems(
                f"Spot {index + 1}" for index in range(len(traps))
            )
            self.optical_trap_selector.setCurrentIndex(0)
        finally:
            self.optical_trap_selector.blockSignals(signals_were_blocked)

        self._apply_optical_trap_to_widgets(self.optical_traps[0])
        self._send_optical_traps_to_slm()

    def _create_circular_pattern(self):
        """Create equally spaced spots around the configured circle."""

        spot_count = self.pattern_spot_count_spin.value()
        radius = self.pattern_radius_spin.value()
        origin_x = self.pattern_origin_x_spin.value()
        origin_y = self.pattern_origin_y_spin.value()

        traps = []
        for index in range(spot_count):
            angle = math.tau * index / spot_count
            traps.append({
                "x": round(origin_x + radius * math.cos(angle), 12),
                "y": round(origin_y + radius * math.sin(angle), 12),
                "z": 0.0,
                "intensity": 1.0,
                "vortex": 0.0,
                "phase": 0.0,
            })

        self._replace_optical_traps(traps)
        self.status_bar.showMessage(
            f"Created {spot_count} spots on a circle of radius {radius:g}",
            3000,
        )

    def _on_pattern_parameter_changed(self):
        """Regenerate the circular pattern after any pattern input changes."""

        self._update_pattern_radius_limit()
        self._create_circular_pattern()

    def _schedule_pattern_update(self):
        """Debounce edits while a pattern value is being typed."""

        if self._pattern_update_in_progress:
            return
        self._pattern_update_timer.start()

    def _apply_pattern_update(self):
        """Commit pending editor text and regenerate the pattern once."""

        if self._pattern_update_in_progress:
            return

        self._pattern_update_timer.stop()
        self._pattern_update_in_progress = True
        try:
            # QSpinBox/QDoubleSpinBox can display newly typed text before their
            # value() has been committed. Explicit interpretation makes the
            # automatic update use exactly what is visible in every field.
            for parameter in self._pattern_parameters:
                parameter.interpretText()
            self._on_pattern_parameter_changed()
        finally:
            self._pattern_update_in_progress = False

    def _update_pattern_radius_limit(self):
        """Keep the generated circle inside the Spots-tab X/Y ranges."""

        origin_x = self.pattern_origin_x_spin.value()
        origin_y = self.pattern_origin_y_spin.value()
        maximum_radius = min(
            origin_x - self.trap_x_spin.minimum(),
            self.trap_x_spin.maximum() - origin_x,
            origin_y - self.trap_y_spin.minimum(),
            self.trap_y_spin.maximum() - origin_y,
        )
        # Updating the maximum can clamp the current radius and emit another
        # valueChanged signal. Block that nested signal because the caller will
        # regenerate the pattern once after the limit has been applied.
        signals_were_blocked = self.pattern_radius_spin.blockSignals(True)
        try:
            self.pattern_radius_spin.setMaximum(max(0.0, maximum_radius))
        finally:
            self.pattern_radius_spin.blockSignals(signals_were_blocked)

    def _send_optical_traps_to_slm(self):
        """Send the current optical trap configuration to the SLM via UDP.

        Safe to call whenever traps are added/removed or their
        parameters are changed.
        """

        if not hasattr(self, "optical_traps"):
            return

        # The noCam backend exposes set_spots(); real camera controllers do
        # not, so this has no effect on the Ximea path.
        ui_methods = getattr(self, "ui_methods", None)
        camera_control = getattr(ui_methods, "camera_control", None)
        update_mock_spots = getattr(camera_control, "set_spots", None)
        if callable(update_mock_spots):
            try:
                update_mock_spots(self.optical_traps)
            except Exception as e:
                logger.error(f"Error updating noCam hologram spots: {e}")

        try:
            # send_traps knows how to map the generic dicts into the
            # UdpHoloMessage structure.
            logger.debug(f"Sending {len(self.optical_traps)} trap(s) to SLM: {self.optical_traps}")
            send_traps(self.optical_traps)
        except Exception as e:
            # Log errors but avoid crashing the UI if the SLM is
            # unreachable.
            import logging

            logging.getLogger(__name__).error(f"Error sending traps to SLM: {e}")

        # Camera overlays and the mock hologram should still update if the SLM
        # UDP endpoint is unavailable.
        self._update_spot_markers_on_camera()

    def _update_spot_markers_on_camera(self):
        """Project optical trap positions onto the camera image.

        The camera-centre controls specify which trap-space coordinate lies
        at the centre of the displayed camera image. +x is to the right; +y
        is up (so image y is inverted).
        """

        # UIMethods is attached by app.py after construction.
        ui_methods = getattr(self, "ui_methods", None)
        if ui_methods is None:
            return

        if not hasattr(self, "optical_traps") or not self.optical_traps:
            ui_methods.set_spot_positions([])
            return

        # Get the original camera image size from the display helper.
        image_display = getattr(ui_methods, "image_display", None)
        if image_display is None or image_display.original_image_size is None:
            # No image yet; nothing to draw.
            return

        width, height = image_display.original_image_size
        image_centre_x = width / 2.0
        image_centre_y = height / 2.0

        camera_centre_x = self.camera_centre_x_spin.value()
        camera_centre_y = self.camera_centre_y_spin.value()

        spots_px = []
        for t in self.optical_traps:
            try:
                x_um = float(t.get("x", 0.0))
                y_um = float(t.get("y", 0.0))
            except (TypeError, ValueError):
                continue

            x_px = image_centre_x + (
                x_um - camera_centre_x
            ) * CAMERA_PIXELS_PER_UM
            # Invert y so +y in trap space is upwards on the image.
            y_px = image_centre_y - (
                y_um - camera_centre_y
            ) * CAMERA_PIXELS_PER_UM

            spots_px.append((x_px, y_px))

        ui_methods.set_spot_positions(spots_px)

    def _on_slm_scale_changed(self):
        """Apply calibration scale factors and refresh the SLM payload."""

        set_coordinate_scales(
            self.slm_x_scale_spin.value(),
            self.slm_y_scale_spin.value(),
            self.slm_z_scale_spin.value(),
        )
        self._send_optical_traps_to_slm()
    
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

        # Estimated acquisition info (time and HDF5 size)
        self.experiment_est_time_label = QLabel("Estimated time: -")
        self.experiment_est_size_label = QLabel("Estimated size: -")

        layout.addWidget(mode_row)
        layout.addWidget(dir_row)
        layout.addWidget(name_row)
        layout.addWidget(fr_row)
        layout.addWidget(frames_row)
        layout.addWidget(self.experiment_est_time_label)
        layout.addWidget(self.experiment_est_size_label)

        # Connect browse button to QFileDialog
        def _browse_dir():
            directory = QFileDialog.getExistingDirectory(self, "Select Experiment Directory")
            if directory:
                self.experiment_dir_edit.setText(directory)

        browse_button.clicked.connect(_browse_dir)

        return group

    def setup_optical_trap_controls(self):
        """Create controls for optical trap (spot) parameters.

        Displayed inside a titled group box "Optical Trap Settings" and
        supports multiple spots with per-spot parameters.
        """

        group = QGroupBox("Optical Trap Settings")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)

        # Internal storage for per-spot parameter dictionaries
        self.optical_traps = []

        # --- Spot selection + add/remove row ---
        selector_row = QWidget()
        selector_layout = QHBoxLayout(selector_row)
        selector_layout.setContentsMargins(0, 0, 0, 0)

        selector_label = QLabel("Spot:")
        self.optical_trap_selector = QComboBox()
        self.optical_trap_add_button = QPushButton("Add")
        self.optical_trap_remove_button = QPushButton("Remove")

        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.optical_trap_selector)
        selector_layout.addWidget(self.optical_trap_add_button)
        selector_layout.addWidget(self.optical_trap_remove_button)

        layout.addWidget(selector_row)

        # --- Parameter rows ---
        def make_param_row(label_text, attr_name, minimum, maximum, step, decimals=3):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(label_text)
            spin = QDoubleSpinBox()
            spin.setRange(minimum, maximum)
            spin.setSingleStep(step)
            spin.setDecimals(decimals)

            row_layout.addWidget(label)
            row_layout.addWidget(spin)

            setattr(self, attr_name, spin)
            return row, spin

        rows_and_spins = []
        rows_and_spins.append(make_param_row("Intensity:", "trap_intensity_spin", 0.0, 1.0, 0.01))
        rows_and_spins.append(make_param_row("X:", "trap_x_spin", -100.0, 100.0, 0.1))
        rows_and_spins.append(make_param_row("Y:", "trap_y_spin", -100.0, 100.0, 0.1))
        rows_and_spins.append(make_param_row("Z:", "trap_z_spin", -100.0, 100.0, 0.1))
        rows_and_spins.append(make_param_row("Vortex:", "trap_vortex_spin", -100.0, 100.0, 1.0))
        rows_and_spins.append(make_param_row("Phase:", "trap_phase_spin", 0.0, 360.0, 1.0, decimals=1))

        for row, _spin in rows_and_spins:
            layout.addWidget(row)

        # Map widget attributes to parameter keys used in internal storage
        self._optical_trap_param_map = {
            "trap_intensity_spin": "intensity",
            "trap_x_spin": "x",
            "trap_y_spin": "y",
            "trap_z_spin": "z",
            "trap_vortex_spin": "vortex",
            "trap_phase_spin": "phase",
        }

        # Connect signals for per-parameter updates
        for attr_name, param_key in self._optical_trap_param_map.items():
            spin = getattr(self, attr_name)

            def _make_handler(key):
                return lambda value, pkey=key: self._on_optical_trap_param_changed(pkey, value)

            spin.valueChanged.connect(_make_handler(param_key))

        # Wire up selector + add/remove behaviour
        self.optical_trap_selector.currentIndexChanged.connect(self._on_optical_trap_changed)
        self.optical_trap_add_button.clicked.connect(self._add_optical_trap)
        self.optical_trap_remove_button.clicked.connect(self._remove_optical_trap)

        # Start with a single default spot
        self._add_optical_trap()

        return group

    def setup_slm_control_tabs(self):
        """Create tabbed controls for SLM spots, patterns, and calibration."""

        self.slm_control_tabs = QTabWidget()
        self.slm_control_tabs.setObjectName("slm_control_tabs")

        self.spots_tab = self.setup_optical_trap_controls()

        self.patterns_control = self.setup_pattern_controls()
        self.calibration_control = self.setup_calibration_controls()

        self.slm_control_tabs.addTab(self.spots_tab, "Spots")
        self.slm_control_tabs.addTab(self.patterns_control, "Patterns")
        self.slm_control_tabs.addTab(self.calibration_control, "Calibration")

        return self.slm_control_tabs

    def setup_pattern_controls(self):
        """Create controls for an equally spaced circular spot pattern."""

        page = QWidget()
        page.setObjectName("patterns_control")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        group = QGroupBox("Circular Spot Pattern")
        layout = QGridLayout(group)

        self.pattern_spot_count_spin = QSpinBox()
        self.pattern_spot_count_spin.setRange(1, 100)
        self.pattern_spot_count_spin.setValue(8)
        self.pattern_spot_count_spin.setToolTip(
            "Number of spots distributed evenly around the circle"
        )

        self.pattern_radius_spin = QDoubleSpinBox()
        self.pattern_radius_spin.setRange(0.0, 100.0)
        self.pattern_radius_spin.setDecimals(3)
        self.pattern_radius_spin.setSingleStep(0.1)
        self.pattern_radius_spin.setValue(10.0)
        self.pattern_radius_spin.setToolTip("Circle radius in trap-coordinate units")

        self.pattern_origin_x_spin = QDoubleSpinBox()
        self.pattern_origin_x_spin.setRange(
            self.trap_x_spin.minimum(), self.trap_x_spin.maximum()
        )
        self.pattern_origin_x_spin.setDecimals(3)
        self.pattern_origin_x_spin.setSingleStep(0.1)
        self.pattern_origin_x_spin.setToolTip("X coordinate of the circle centre")

        self.pattern_origin_y_spin = QDoubleSpinBox()
        self.pattern_origin_y_spin.setRange(
            self.trap_y_spin.minimum(), self.trap_y_spin.maximum()
        )
        self.pattern_origin_y_spin.setDecimals(3)
        self.pattern_origin_y_spin.setSingleStep(0.1)
        self.pattern_origin_y_spin.setToolTip("Y coordinate of the circle centre")

        layout.addWidget(QLabel("Number of spots (N):"), 0, 0)
        layout.addWidget(self.pattern_spot_count_spin, 0, 1)
        layout.addWidget(QLabel("Radius (r):"), 1, 0)
        layout.addWidget(self.pattern_radius_spin, 1, 1)
        layout.addWidget(QLabel("Origin X:"), 2, 0)
        layout.addWidget(self.pattern_origin_x_spin, 2, 1)
        layout.addWidget(QLabel("Origin Y:"), 3, 0)
        layout.addWidget(self.pattern_origin_y_spin, 3, 1)

        self._pattern_parameters = (
            self.pattern_spot_count_spin,
            self.pattern_radius_spin,
            self.pattern_origin_x_spin,
            self.pattern_origin_y_spin,
        )

        self._pattern_update_in_progress = False
        self._pattern_update_timer = QTimer(self)
        self._pattern_update_timer.setSingleShot(True)
        self._pattern_update_timer.setInterval(200)
        self._pattern_update_timer.timeout.connect(self._apply_pattern_update)

        self.pattern_create_button = QPushButton("Create pattern")
        self.pattern_create_button.clicked.connect(self._apply_pattern_update)
        layout.addWidget(self.pattern_create_button, 4, 0, 1, 2)

        for parameter in self._pattern_parameters:
            parameter.textChanged.connect(
                lambda _text: self._schedule_pattern_update()
            )

        self._update_pattern_radius_limit()

        page_layout.addWidget(group)
        return page

    def setup_calibration_controls(self):
        """Create camera-overlay and SLM coordinate calibration controls."""

        page = QWidget()
        page.setObjectName("calibration_control")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        camera_group = QGroupBox("Camera Overlay Alignment")
        camera_layout = QGridLayout(camera_group)

        self.camera_centre_x_spin = QDoubleSpinBox()
        self.camera_centre_x_spin.setRange(-100.0, 100.0)
        self.camera_centre_x_spin.setSingleStep(0.1)
        self.camera_centre_x_spin.setDecimals(3)
        self.camera_centre_x_spin.setToolTip(
            "Trap X coordinate located at the centre of the camera image"
        )

        self.camera_centre_y_spin = QDoubleSpinBox()
        self.camera_centre_y_spin.setRange(-100.0, 100.0)
        self.camera_centre_y_spin.setSingleStep(0.1)
        self.camera_centre_y_spin.setDecimals(3)
        self.camera_centre_y_spin.setToolTip(
            "Trap Y coordinate located at the centre of the camera image"
        )

        camera_layout.addWidget(QLabel("Camera centre X (µm):"), 0, 0)
        camera_layout.addWidget(self.camera_centre_x_spin, 0, 1)
        camera_layout.addWidget(QLabel("Camera centre Y (µm):"), 1, 0)
        camera_layout.addWidget(self.camera_centre_y_spin, 1, 1)
        page_layout.addWidget(camera_group)

        scales_group = QGroupBox("SLM Coordinate Scaling")
        scales_layout = QGridLayout(scales_group)
        x_scale, y_scale, z_scale = get_coordinate_scales()

        scale_controls = (
            ("X_SCALE:", "slm_x_scale_spin", x_scale),
            ("Y_SCALE:", "slm_y_scale_spin", y_scale),
            ("Z_SCALE:", "slm_z_scale_spin", z_scale),
        )
        for row, (label, attr_name, value) in enumerate(scale_controls):
            spin = QDoubleSpinBox()
            spin.setRange(-1.0, 1.0)
            spin.setDecimals(10)
            spin.setSingleStep(0.0000001)
            spin.setValue(value)
            spin.setToolTip(
                "Multiplier applied to this trap coordinate before sending it to the SLM"
            )
            setattr(self, attr_name, spin)
            scales_layout.addWidget(QLabel(label), row, 0)
            scales_layout.addWidget(spin, row, 1)

        page_layout.addWidget(scales_group)

        # Camera alignment only moves the overlay.
        self.camera_centre_x_spin.valueChanged.connect(
            lambda _value: self._update_spot_markers_on_camera()
        )
        self.camera_centre_y_spin.valueChanged.connect(
            lambda _value: self._update_spot_markers_on_camera()
        )

        # Scale changes immediately rebuild and send the current SLM payload.
        for spin in (
            self.slm_x_scale_spin,
            self.slm_y_scale_spin,
            self.slm_z_scale_spin,
        ):
            spin.valueChanged.connect(lambda _value: self._on_slm_scale_changed())

        return page
    
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
        # SLM spot and pattern controls
        controls_narrow_layout.addWidget(self.setup_slm_control_tabs())
        # Experiment / time-series configuration controls
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

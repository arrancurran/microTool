"""
Base classes for camera controls.
"""
from PyQt6.QtCore import QTimer
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QSlider
import logging
from typing import Any

# Configure logging for this module
logger = logging.getLogger(__name__)

class CameraControl(ABC):
    """Base class for all camera controls."""
    def __init__(self, camera_control, window):
        logger.debug("Initializing base camera control")
        self.camera_control = camera_control
        self.window = window
        self.pending_value = None
        
        # Setup debounce timer
        self.control_timer = QTimer()
        self.control_timer.setSingleShot(True)
        self.control_timer.timeout.connect(self._apply_change)
        logger.debug("Initialized control timer")
        
    @abstractmethod
    def setup_ui(self):
        """Setup the UI elements for this control."""
        pass
        
    @abstractmethod
    def handle_value_change(self, value: Any) -> None:
        """Handle changes to the control's value.
        
        This is the entry point for all value changes. Subclasses should implement
        their specific handling logic while preserving any parent class behavior.
        """
        pass
        
    @abstractmethod
    def _apply_change(self) -> None:
        """Apply the pending change to the camera."""
        pass

class NumericCameraControl(CameraControl):
    """Base class for numeric camera controls (exposure, gain, etc.)."""
    def __init__(self, camera_control, window, command_name: str, display_name: str):
        super().__init__(camera_control, window)
        self.command_name = command_name
        self.display_name = display_name
        # Create a logger specific to this control instance
        self.logger = logging.getLogger(f"camera_controls.{command_name}")
        logger.debug(f"Initialized {display_name} control with command: {command_name}")
        
    def setup_ui(self):
        """Get min/max from camera and setup the UI."""
        try:
            logger.debug(f"Getting {self.display_name} settings from camera...")
            
            # Get min/max/current values using command names from commands.json
            min_val = self.camera_control.call_camera_command(f"{self.command_name}_min", "get")
            max_val = self.camera_control.call_camera_command(f"{self.command_name}_max", "get")
            current = self.camera_control.call_camera_command(self.command_name, "get")
            
            logger.debug(f"{self.display_name} settings - min: {min_val}, max: {max_val}, current: {current}")
            
            if all(v is not None for v in [min_val, max_val, current]):
                return {
                    'min': min_val,
                    'max': max_val,
                    'current': current
                }
            else:
                logger.warning(f"Some {self.display_name} settings are None")
                return None
                
        except Exception as e:
            logger.error(f"Error getting {self.display_name} settings: {str(e)}")
            return None
        
    def handle_value_change(self, value: float) -> None:
        """Queue value change with debouncing.
        
        This implementation handles the debouncing logic for numeric controls.
        Subclasses should call this method after their specific handling.
        """
        self.logger.debug(f"{self.display_name} value change queued: {value}")
        self.pending_value = value
        self.control_timer.start(50)  # 50ms debounce
        
    def _apply_change(self) -> None:
        """Apply the pending change to the camera."""
        if self.pending_value is not None:
            try:
                self.logger.debug(f"Applying {self.display_name} change: {self.pending_value}")
                self.camera_control.call_camera_command(self.command_name, "set", self.pending_value)
                logger.debug(f"{self.display_name} change applied successfully")
                
                # Update status bar if available
                if hasattr(self.window, 'ui_methods') and hasattr(self.window.ui_methods, 'status_bar_manager'):
                    self.window.ui_methods.status_bar_manager.update_on_control_change(self.command_name)
                
                self.pending_value = None
            except Exception as e:
                logger.error(f"Error setting {self.display_name}: {str(e)}")
                self.pending_value = None  # Clear pending value on error 

class SliderControl(NumericCameraControl):
    """Generic slider-based camera control."""
    
    def __init__(self, camera_control, window, command_name: str, display_name: str, 
                 slider_attr: str, label_attr: str, formatter=None):
        super().__init__(camera_control, window, command_name, display_name)
        self.slider_attr = slider_attr
        self.label_attr = label_attr
        self.formatter = formatter or (lambda x: f"{self.display_name}: {x}")
        
    def setup_ui(self) -> bool:
        """Set up the slider UI elements."""
        try:
            # Get UI elements
            slider = getattr(self.window, self.slider_attr, None)
            label = getattr(self.window, self.label_attr, None)
            
            if not slider or not label:
                self.logger.error(f"Missing UI elements: {self.slider_attr}, {self.label_attr}")
                return False
                
            # Get settings from camera
            settings = super().setup_ui()
            if not settings:
                return False
                
            # Configure slider
            min_val = int(round(settings['min']))
            max_val = int(round(settings['max']))
            current = int(round(settings['current']))
            
            slider.setMinimum(min_val)
            slider.setMaximum(max_val)
            
            # Setup signal connection
            try:
                slider.valueChanged.disconnect()
            except Exception:
                pass
            slider.valueChanged.connect(self.handle_value_change)
            
            # Set initial value
            slider.setValue(current)
            self._update_label(current)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up UI: {str(e)}")
            return False
            
    def _update_label(self, value: float) -> None:
        """Update the label with formatted value."""
        try:
            label = getattr(self.window, self.label_attr)
            label.setText(self.formatter(value))
        except Exception as e:
            self.logger.error(f"Error updating label: {str(e)}")
            
    def handle_value_change(self, value: float) -> None:
        """Handle slider value changes.
        
        This implementation:
        1. Updates the UI label with the new value
        2. Calls the parent's implementation to handle debouncing
        """
        self._update_label(value)
        super().handle_value_change(float(value)) 
"""
Base classes for camera controls.
"""
from PyQt6.QtCore import QTimer
from abc import ABC, abstractmethod

class CameraControl(ABC):
    """Base class for all camera controls."""
    def __init__(self, camera_control, window):
        print(f"Initializing base camera control")  # Debug print
        self.camera_control = camera_control
        self.window = window
        self.pending_value = None
        
        # Setup debounce timer
        self.control_timer = QTimer()
        self.control_timer.setSingleShot(True)
        self.control_timer.timeout.connect(self._apply_change)
        print("Initialized control timer")  # Debug print
        
    @abstractmethod
    def setup_ui(self):
        """Setup the UI elements for this control."""
        pass
        
    @abstractmethod
    def handle_value_change(self, value):
        """Handle changes to the control's value."""
        pass
        
    @abstractmethod
    def _apply_change(self):
        """Apply the pending change to the camera."""
        pass

class NumericCameraControl(CameraControl):
    """Base class for numeric camera controls (exposure, gain, etc.)."""
    def __init__(self, camera_control, window, command_name, display_name):
        super().__init__(camera_control, window)
        self.command_name = command_name
        self.display_name = display_name
        print(f"Initialized {display_name} control with command: {command_name}")  # Debug print
        
    def setup_ui(self):
        """Get min/max from camera and setup the UI."""
        try:
            print(f"Getting {self.display_name} settings from camera...")  # Debug print
            
            # Get min/max/current values using command names from commands.json
            min_val = self.camera_control.call_camera_command(f"{self.command_name}_min", "get")
            max_val = self.camera_control.call_camera_command(f"{self.command_name}_max", "get")
            current = self.camera_control.call_camera_command(self.command_name, "get")
            
            print(f"{self.display_name} settings - min: {min_val}, max: {max_val}, current: {current}")  # Debug print
            
            if all(v is not None for v in [min_val, max_val, current]):
                return {
                    'min': min_val,
                    'max': max_val,
                    'current': current
                }
            else:
                print(f"Some {self.display_name} settings are None")  # Debug print
                return None
                
        except Exception as e:
            print(f"Error getting {self.display_name} settings: {str(e)}")  # Debug print
            return None
        
    def handle_value_change(self, value):
        """Queue value change with debouncing."""
        print(f"{self.display_name} value change queued: {value}")  # Debug print
        self.pending_value = value
        self.control_timer.start(50)  # 50ms debounce
        
    def _apply_change(self):
        """Apply the pending change to the camera."""
        if self.pending_value is not None:
            try:
                print(f"Applying {self.display_name} change: {self.pending_value}")  # Debug print
                self.camera_control.call_camera_command(self.command_name, "set", self.pending_value)
                print(f"{self.display_name} change applied successfully")  # Debug print
                self.pending_value = None
            except Exception as e:
                print(f"Error setting {self.display_name}: {str(e)}")
                self.pending_value = None  # Clear pending value on error 
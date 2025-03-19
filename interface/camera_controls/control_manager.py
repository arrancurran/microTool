"""
Manager for all camera controls.
"""
from typing import Dict, Type

from .base_control import CameraControl
from .exposure_control import ExposureControl
from .roi_control import ROIControl

class CameraControlManager:
    """Manages all camera controls and their initialization."""
    
    # Register new control types here
    CONTROL_TYPES = {
        'exposure': ExposureControl,
        'roi': ROIControl,
        # Add new controls like:
        # 'gain': GainControl,
        # 'framerate': FramerateControl,
    }
    
    def __init__(self, camera_control, window):
        print("Initializing CameraControlManager")  # Debug print
        self.camera_control = camera_control
        self.window = window
        self.controls: Dict[str, CameraControl] = {}
        
    def initialize_controls(self):
        """Initialize all registered control types."""
        print(f"Initializing {len(self.CONTROL_TYPES)} camera controls...")  # Debug print
        for control_name, control_class in self.CONTROL_TYPES.items():
            print(f"Setting up {control_name} control...")  # Debug print
            try:
                control = control_class(self.camera_control, self.window)
                if control.setup_ui():
                    self.controls[control_name] = control
                    print(f"Successfully initialized {control_name} control")
                else:
                    print(f"Failed to initialize {control_name} control - setup_ui returned False")
            except Exception as e:
                print(f"Error initializing {control_name} control: {str(e)}")
        print(f"Finished initializing controls. Active controls: {list(self.controls.keys())}")  # Debug print
    
    def get_control(self, control_name: str) -> CameraControl:
        """Get a specific control by name."""
        control = self.controls.get(control_name)
        if control is None:
            print(f"Warning: Control '{control_name}' not found")  # Debug print
        return control
    
    def cleanup(self):
        """Cleanup all controls."""
        print("Cleaning up camera controls...")  # Debug print
        for control_name, control in self.controls.items():
            try:
                if hasattr(control, 'cleanup'):
                    control.cleanup()
                    print(f"Cleaned up {control_name} control")  # Debug print
            except Exception as e:
                print(f"Error cleaning up {control_name} control: {str(e)}")
        print("Finished cleaning up controls")  # Debug print 
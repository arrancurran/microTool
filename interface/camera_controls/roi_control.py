"""
ROI (Region of Interest) controls for the camera.
"""
from PyQt6.QtWidgets import QSpinBox
from .base_control import NumericCameraControl

class ROIControl(NumericCameraControl):
    """Control for camera ROI settings (width, height, offset_x, offset_y)."""
    
    def __init__(self, camera_control, window):
        print("Initializing ROIControl")  # Debug print
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="roi",  # Not actually used, we handle commands directly
            display_name="ROI"
        )
        # Store the spinboxes for easy access
        self.controls = {
            'width': (self.window.roi_width, 'width'),
            'height': (self.window.roi_height, 'height'),
            'offset_x': (self.window.roi_offset_x, 'offset_x'),
            'offset_y': (self.window.roi_offset_y, 'offset_y')
        }
        
    def setup_ui(self) -> bool:
        """Set up the ROI UI elements."""
        print("Setting up ROI controls")  # Debug print
        
        # Check if UI elements exist
        for name, (spinbox, _) in self.controls.items():
            if not hasattr(self.window, f'roi_{name}'):
                print(f"Error: roi_{name} not found in window")
                return False
        
        try:
            # Get settings for each control
            settings = {}
            for name, (spinbox, cmd_name) in self.controls.items():
                # Get min, max, increment, and current values
                min_val = int(self.camera_control.call_camera_command(f"{cmd_name}_min", "get"))
                max_val = int(self.camera_control.call_camera_command(f"{cmd_name}_max", "get"))
                increment = int(self.camera_control.call_camera_command(f"{cmd_name}_inc", "get"))
                current = int(self.camera_control.call_camera_command(cmd_name, "get"))
                
                print(f"Got {name} settings - min: {min_val}, max: {max_val}, increment: {increment}, current: {current}")
                
                # Configure spinbox
                spinbox.setMinimum(min_val)
                spinbox.setMaximum(max_val)
                spinbox.setSingleStep(increment)  # Set the increment value
                
                # Ensure current value is within bounds and aligned to increment
                current = max(min_val, min(max_val, current))
                current = (current // increment) * increment
                
                # Disconnect any existing connections
                try:
                    spinbox.valueChanged.disconnect()
                except Exception:
                    pass
                
                # Connect new signal
                spinbox.valueChanged.connect(
                    lambda value, cmd=cmd_name: self.handle_roi_change(cmd, value)
                )
                
                # Set initial value
                spinbox.setValue(current)
                print(f"Initialized {name} control with value: {current}, step: {increment}")
            
            return True
            
        except Exception as e:
            print(f"Error setting up ROI controls: {str(e)}")
            return False
    
    def handle_roi_change(self, command_name: str, value: int):
        """Handle changes to any ROI control."""
        print(f"ROI {command_name} changed to: {value}")  # Debug print
        try:
            # Get the increment value
            increment = int(self.camera_control.call_camera_command(f"{command_name}_inc", "get"))
            
            # Ensure value is aligned with increment
            aligned_value = (value // increment) * increment
            if aligned_value != value:
                print(f"Adjusting {command_name} value to align with increment: {value} -> {aligned_value}")
                value = aligned_value
                # Update the spinbox without triggering another change
                for _, (spinbox, cmd) in self.controls.items():
                    if cmd == command_name:
                        spinbox.blockSignals(True)
                        spinbox.setValue(value)
                        spinbox.blockSignals(False)
                        break
            
            self.camera_control.call_camera_command(command_name, "set", value)
            print(f"Successfully applied {command_name} = {value}")
        except Exception as e:
            print(f"Error applying {command_name} value: {str(e)}")
    
    def handle_value_change(self, value):
        """Not used - we handle changes directly in handle_roi_change."""
        pass
    
    def _apply_change(self):
        """Not used - we handle changes directly in handle_roi_change."""
        pass 
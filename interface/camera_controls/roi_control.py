"""Controls for camera Region of Interest (ROI) settings - width, height, and offsets."""
from .base_control import NumericCameraControl

class ROIControl(NumericCameraControl):
    """
    Controls camera Region of Interest (ROI) settings via spinboxes in the UI.
    Called by the main app to initialize camera controls.
    Example usage:
        roi_control = ROIControl(camera_control, window)
        roi_control.setup_ui()  # Configures spinboxes with camera's ROI limits
    """
    
    def __init__(self, camera_control, window):
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="roi",  # Not actually used, we handle commands directly
            display_name="ROI"
        )
        # Store references to spinboxes and their corresponding camera commands
        self.controls = {
            'width': (window.roi_width, 'width'),
            'height': (window.roi_height, 'height'),
            'offset_x': (window.roi_offset_x, 'offset_x'),
            'offset_y': (window.roi_offset_y, 'offset_y')
        }
        
        # Cache for max dimensions
        self.max_dimensions = None
        
    def setup_ui(self) -> bool:
        """Set up the ROI UI elements."""
        try:
            # Get max dimensions first
            self.max_dimensions = {
                'width': int(self.camera_control.call_camera_command("width_max", "get")),
                'height': int(self.camera_control.call_camera_command("height_max", "get"))
            }
            
            # Setup each control
            for name, (spinbox, cmd_name) in self.controls.items():
                # Get min, max, increment values
                min_val = int(self.camera_control.call_camera_command(f"{cmd_name}_min", "get"))
                max_val = int(self.camera_control.call_camera_command(f"{cmd_name}_max", "get"))
                increment = int(self.camera_control.call_camera_command(f"{cmd_name}_inc", "get"))
                current = int(self.camera_control.call_camera_command(cmd_name, "get"))
                
                # Configure spinbox
                spinbox.setMinimum(min_val)
                spinbox.setMaximum(max_val)
                spinbox.setSingleStep(increment)
                
                # Ensure current value is valid
                current = self._validate_value(name, current, increment)
                
                # Connect signal
                try:
                    spinbox.valueChanged.disconnect()
                except Exception:
                    pass
                
                spinbox.valueChanged.connect(
                    lambda value, n=name: self.handle_roi_change(n, value)
                )
                
                # Set initial value
                spinbox.setValue(current)
            
            return True
            
        except Exception as e:
            print(f"Error setting up ROI controls: {str(e)}")
            return False
    
    def _validate_value(self, name: str, value: int, increment: int) -> int:
        """Validate and adjust ROI values."""
        # Align to increment
        value = (value // increment) * increment
        
        # Get current values for validation using self.controls
        current_values = {
            control_name: spinbox.value()
            for control_name, (spinbox, _) in self.controls.items()
        }
        
        # Validate against max dimensions for offsets and dimensions
        if name == 'offset_x':
            max_offset = self.max_dimensions['width'] - current_values['width']
            value = min(value, max_offset)
        elif name == 'offset_y':
            max_offset = self.max_dimensions['height'] - current_values['height']
            value = min(value, max_offset)
        elif name == 'width':
            max_width = self.max_dimensions['width'] - current_values['offset_x']
            value = min(value, max_width)
        elif name == 'height':
            max_height = self.max_dimensions['height'] - current_values['offset_y']
            value = min(value, max_height)
            
        return value
    
    def handle_roi_change(self, name: str, value: int, update_related: bool = True):
        """Unified handler for all ROI changes.
        
        Args:
            name: Name of the control being changed
            value: New value to set
            update_related: Whether to update related controls (default: True)
        """
        try:
            # Get increment for alignment
            cmd_name = self.controls[name][1]
            increment = int(self.camera_control.call_camera_command(f"{cmd_name}_inc", "get"))
            
            # Validate and adjust value
            value = self._validate_value(name, value, increment)
            
            # Update spinbox if value was adjusted
            spinbox = self.controls[name][0]
            if spinbox.value() != value:
                spinbox.blockSignals(True)
                spinbox.setValue(value)
                spinbox.blockSignals(False)
            
            # Apply to camera
            self.camera_control.call_camera_command(cmd_name, "set", value)
            
            # Update related limits if requested
            if update_related:
                self._update_related_limits(name)
            
            # Update status bar
            if hasattr(self.window, 'ui_methods') and hasattr(self.window.ui_methods, 'status_bar_manager'):
                self.window.ui_methods.status_bar_manager.update_on_control_change("roi")
                
        except Exception as e:
            print(f"Error handling ROI change: {str(e)}")
    
    def _update_related_limits(self, changed_control: str):
        """Update limits for related controls when one control changes."""
        # Define relationships between controls
        relationships = {
            'width': ['offset_x'],
            'height': ['offset_y'],
            'offset_x': ['width'],
            'offset_y': ['height']
        }
        
        # Update each related control
        for related in relationships[changed_control]:
            # Determine if we're updating an offset or dimension
            is_offset = changed_control in ['width', 'height']
            dimension = related.split('_')[0] if is_offset else related
            
            # Calculate new maximum
            new_max = self.max_dimensions[dimension] - self.controls[changed_control][0].value()
            self.controls[related][0].setMaximum(new_max)
            
            # Adjust value if needed
            current_value = self.controls[related][0].value()
            if current_value > new_max:
                # Use handle_roi_change with update_related=False to prevent recursion
                self.handle_roi_change(related, new_max, update_related=False) 
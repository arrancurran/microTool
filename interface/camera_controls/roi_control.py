"""
ROI (Region of Interest) controls for the camera.
"""
from .base_control import NumericCameraControl

class ROIControl(NumericCameraControl):
    """Control for camera ROI settings (width, height, offset_x, offset_y)."""
    
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
        
        # Validate against max dimensions for offsets and dimensions
        if name == 'offset_x':
            max_offset = self.max_dimensions['width'] - self.window.roi_width.value()
            value = min(value, max_offset)
        elif name == 'offset_y':
            max_offset = self.max_dimensions['height'] - self.window.roi_height.value()
            value = min(value, max_offset)
        elif name == 'width':
            max_width = self.max_dimensions['width'] - self.window.roi_offset_x.value()
            value = min(value, max_width)
        elif name == 'height':
            max_height = self.max_dimensions['height'] - self.window.roi_offset_y.value()
            value = min(value, max_height)
            
        return value
    
    def handle_roi_change(self, name: str, value: int):
        """Unified handler for all ROI changes."""
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
            
            # Update limits based on what changed
            if name in ['width', 'height']:
                self._update_offset_limits(name)
            else:  # offset_x or offset_y
                self._update_dimension_limits(name)
            
            # Update status bar
            if hasattr(self.window, 'ui_methods') and hasattr(self.window.ui_methods, 'status_bar_manager'):
                self.window.ui_methods.status_bar_manager.update_on_control_change("roi")
                
        except Exception as e:
            print(f"Error handling ROI change: {str(e)}")
    
    def _update_offset_limits(self, changed_dimension: str):
        """Update offset limits when width/height changes."""
        if changed_dimension == 'width':
            new_offset_max = self.max_dimensions['width'] - self.window.roi_width.value()
            self.window.roi_offset_x.setMaximum(new_offset_max)
            
            # Adjust offset if needed
            current_offset = self.window.roi_offset_x.value()
            if current_offset > new_offset_max:
                self.handle_roi_change('offset_x', new_offset_max)
                
        else:  # height
            new_offset_max = self.max_dimensions['height'] - self.window.roi_height.value()
            self.window.roi_offset_y.setMaximum(new_offset_max)
            
            # Adjust offset if needed
            current_offset = self.window.roi_offset_y.value()
            if current_offset > new_offset_max:
                self.handle_roi_change('offset_y', new_offset_max)
    
    def _update_dimension_limits(self, changed_offset: str):
        """Update width/height limits when offsets change."""
        if changed_offset == 'offset_x':
            new_width_max = self.max_dimensions['width'] - self.window.roi_offset_x.value()
            self.window.roi_width.setMaximum(new_width_max)
            
            # Adjust width if needed
            current_width = self.window.roi_width.value()
            if current_width > new_width_max:
                self.handle_roi_change('width', new_width_max)
                
        else:  # offset_y
            new_height_max = self.max_dimensions['height'] - self.window.roi_offset_y.value()
            self.window.roi_height.setMaximum(new_height_max)
            
            # Adjust height if needed
            current_height = self.window.roi_height.value()
            if current_height > new_height_max:
                self.handle_roi_change('height', new_height_max)
    
    def handle_value_change(self, value):
        """Not used - we handle changes directly in handle_roi_change."""
        pass
    
    def _apply_change(self):
        """Not used - we handle changes directly in handle_roi_change."""
        pass 
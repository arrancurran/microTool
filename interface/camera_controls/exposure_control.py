"""
Exposure control for the camera.
"""
from PyQt6.QtWidgets import QSlider
from PyQt6.QtCore import Qt

from .base_control import NumericCameraControl

class ExposureControl(NumericCameraControl):
    """Control for camera exposure settings."""
    
    def __init__(self, camera_control, window):
        print("Initializing ExposureControl")  # Debug print
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="exposure",
            display_name="Exposure"
        )
        
    def setup_ui(self) -> bool:
        """Set up the exposure UI elements."""
        print("Setting up exposure UI elements")  # Debug print
        
        # Check if UI elements exist
        if not hasattr(self.window, 'exposure_slider'):
            print("Error: exposure_slider not found in window")
            return False
        if not hasattr(self.window, 'exposure_label'):
            print("Error: exposure_label not found in window")
            return False
            
        print("Found required UI elements")
        
        try:
            # Get settings from camera
            settings = super().setup_ui()
            if not settings:
                print("Failed to get exposure settings from camera")
                return False
                
            print(f"Got exposure settings: {settings}")  # Debug print
            
            # Convert float values to integers for the slider
            min_val = int(round(settings['min']))
            max_val = int(round(settings['max']))
            current = int(round(settings['current']))
            
            print(f"Converted values for slider - min: {min_val}, max: {max_val}, current: {current}")  # Debug print
            
            # Configure the slider
            self.window.exposure_slider.setMinimum(min_val)
            self.window.exposure_slider.setMaximum(max_val)
            print(f"Configured slider with range: {min_val} to {max_val}")  # Debug print
            
            # Disconnect any existing connections to prevent duplicates
            try:
                self.window.exposure_slider.valueChanged.disconnect()
                print("Disconnected existing slider connections")  # Debug print
            except Exception:
                print("No existing connections to disconnect")  # Debug print
                
            # Connect the new signal
            self.window.exposure_slider.valueChanged.connect(self.handle_value_change)
            print("Connected slider to handle_value_change")  # Debug print
            
            # Set initial value and update label
            self.window.exposure_slider.setValue(current)
            self._format_and_update_label(current)
            
            return True
            
        except Exception as e:
            print(f"Error setting up exposure UI: {str(e)}")
            return False
    
    def _format_and_update_label(self, value):
        """Format and update the exposure label."""
        try:
            if value >= 1000:
                formatted_value = f"Exposure: {value/1000:.1f} ms"
            else:
                formatted_value = f"Exposure: {value} μs"
            self.window.exposure_label.setText(formatted_value)
            print(f"Updated exposure label to: {formatted_value}")  # Debug print
        except Exception as e:
            print(f"Error updating exposure label: {str(e)}")
    
    def handle_value_change(self, value):
        """Handle exposure slider value changes."""
        print(f"Exposure value changed to: {value}")  # Debug print
        self._format_and_update_label(value)
        super().handle_value_change(float(value))  # Convert back to float for camera
        
    def _apply_change(self):
        """Apply the pending exposure change to the camera."""
        if self.pending_value is not None:
            print(f"Applying exposure value: {self.pending_value}")  # Debug print
            try:
                self.camera_control.call_camera_command(self.command_name, "set", self.pending_value)
                print("Successfully applied exposure value")  # Debug print
                self._format_and_update_label(int(round(self.pending_value)))
                self.pending_value = None
            except Exception as e:
                print(f"Error applying exposure value: {str(e)}")
                self.pending_value = None 
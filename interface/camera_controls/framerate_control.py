"""
Framerate control for the camera.
"""
from PyQt6.QtWidgets import QSlider
from PyQt6.QtCore import Qt

from .base_control import NumericCameraControl

class FramerateControl(NumericCameraControl):
    """Control for camera framerate settings."""
    
    def __init__(self, camera_control, window):
        print("Initializing FramerateControl")  # Debug print
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="framerate",
            display_name="Framerate"
        )
        
    def setup_ui(self) -> bool:
        """Set up the framerate UI elements."""
        print("Setting up framerate UI elements")  # Debug print
        
        # Check if UI elements exist
        if not hasattr(self.window, 'framerate_slider'):
            print("Error: framerate_slider not found in window")
            return False
        if not hasattr(self.window, 'framerate_label'):
            print("Error: framerate_label not found in window")
            return False
            
        print("Found required UI elements")
        
        try:
            # Get settings from camera
            settings = super().setup_ui()
            if not settings:
                print("Failed to get framerate settings from camera")
                return False
                
            # Convert float values to integers for the slider
            min_val = int(round(settings['min']))
            max_val = int(round(settings['max']))
            current = int(round(settings['current']))
            
            print(f"Using framerate values - min: {min_val}, max: {max_val}, current: {current}")  # Debug print
            
            # Configure the slider
            self.window.framerate_slider.setMinimum(min_val)
            self.window.framerate_slider.setMaximum(max_val)
            print(f"Configured slider with range: {min_val} to {max_val}")  # Debug print
            
            # Disconnect any existing connections to prevent duplicates
            try:
                self.window.framerate_slider.valueChanged.disconnect()
                print("Disconnected existing slider connections")  # Debug print
            except Exception:
                print("No existing connections to disconnect")  # Debug print
                
            # Connect the new signal
            self.window.framerate_slider.valueChanged.connect(self.handle_value_change)
            print("Connected slider to handle_value_change")  # Debug print
            
            # Set initial value and update label
            self.window.framerate_slider.setValue(current)
            self._format_and_update_label(current)
            
            return True
            
        except Exception as e:
            print(f"Error setting up framerate UI: {str(e)}")
            return False
    
    def _format_and_update_label(self, value):
        """Format and update the framerate label."""
        try:
            formatted_value = f"Framerate: {value:.1f} Hz"
            self.window.framerate_label.setText(formatted_value)
            print(f"Updated framerate label to: {formatted_value}")  # Debug print
        except Exception as e:
            print(f"Error updating framerate label: {str(e)}")
    
    def handle_value_change(self, value):
        """Handle framerate slider value changes."""
        print(f"Framerate value changed to: {value}")  # Debug print
        self._format_and_update_label(value)
        super().handle_value_change(float(value))  # Convert back to float for camera
        
    def _apply_change(self):
        """Apply the pending framerate change to the camera."""
        if self.pending_value is not None:
            print(f"Applying framerate value: {self.pending_value}")  # Debug print
            try:
                self.camera_control.call_camera_command(self.command_name, "set", self.pending_value)
                print("Successfully applied framerate value")  # Debug print
                self._format_and_update_label(self.pending_value)
                
                # Update status bar
                if hasattr(self.window, 'ui_methods') and hasattr(self.window.ui_methods, 'status_bar_manager'):
                    self.window.ui_methods.status_bar_manager.update_on_control_change(self.command_name)
                
                self.pending_value = None
            except Exception as e:
                print(f"Error applying framerate value: {str(e)}")
                self.pending_value = None 
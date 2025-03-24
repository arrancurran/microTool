"""
Manager for updating the status bar with camera information.
"""
from PyQt6.QtCore import QObject
import math

class StatusBarManager(QObject):
    """Manages updates to the status bar with camera information."""
    
    def __init__(self, window, camera_control):
        """Initialize the status bar manager."""
        super().__init__()
        self.window = window
        self.camera_control = camera_control
        
    def update_all(self):
        """Update all status bar labels with current camera information."""
        self.update_camera_model()
        self.update_roi_data()
        self.update_framerate()
        self.update_image_size()
        self.update_streaming_bandwidth()
        
    def update_camera_model(self):
        """Update the camera model label with device name."""
        try:
            if self.camera_control.camera:
                device_name = self.camera_control.camera.get_device_name().decode('utf-8')
                if device_name:
                    self.window.camera_model_label.setText(device_name)
                else:
                    self.window.camera_model_label.setText("No Camera")
            else:
                self.window.camera_model_label.setText("No Camera")
        except Exception as e:
            print(f"Error updating camera model: {str(e)}")
            self.window.camera_model_label.setText("No Camera")
            
    def update_roi_data(self):
        """Update the ROI data label with current width x height."""
        try:
            width = int(self.camera_control.call_camera_command("width", "get"))
            height = int(self.camera_control.call_camera_command("height", "get"))
            self.window.roi_data_label.setText(f"{width}x{height}")
        except Exception as e:
            print(f"Error updating ROI data: {str(e)}")
            self.window.roi_data_label.setText("0x0")
            
    def update_framerate(self):
        """Update the framerate label."""
        try:
            framerate = float(self.camera_control.call_camera_command("framerate", "get"))
            self.window.framerate_label.setText(f"@ {framerate:.1f} Hz")
        except Exception as e:
            print(f"Error updating framerate: {str(e)}")
            self.window.framerate_label.setText("@ 0 Hz")
            
    def update_image_size(self):
        """Update the image size label with appropriate units."""
        try:
            width = int(self.camera_control.call_camera_command("width", "get"))
            height = int(self.camera_control.call_camera_command("height", "get"))
            # Assuming 8-bit grayscale image
            size_bytes = width * height
            
            # Convert to appropriate unit
            if size_bytes >= 1024**3:  # GB
                size_str = f"{size_bytes / (1024**3):.2f} GB"
            elif size_bytes >= 1024**2:  # MB
                size_str = f"{size_bytes / (1024**2):.2f} MB"
            elif size_bytes >= 1024:  # KB
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:  # B
                size_str = f"{size_bytes} B"
                
            self.window.image_size_on_disk_label.setText(size_str)
        except Exception as e:
            print(f"Error updating image size: {str(e)}")
            self.window.image_size_on_disk_label.setText("0.00 MB")
            
    def update_streaming_bandwidth(self):
        """Update the streaming bandwidth label."""
        try:
            # Get current framerate and image size
            framerate = float(self.camera_control.call_camera_command("framerate", "get"))
            width = int(self.camera_control.call_camera_command("width", "get"))
            height = int(self.camera_control.call_camera_command("height", "get"))
            
            # Calculate bandwidth in bytes per second
            bandwidth_bytes_per_sec = width * height * framerate
            
            # Convert to appropriate unit
            if bandwidth_bytes_per_sec >= 1024**3:  # GB/s
                bandwidth_str = f"{bandwidth_bytes_per_sec / (1024**3):.2f} GB/s"
            elif bandwidth_bytes_per_sec >= 1024**2:  # MB/s
                bandwidth_str = f"{bandwidth_bytes_per_sec / (1024**2):.2f} MB/s"
            elif bandwidth_bytes_per_sec >= 1024:  # KB/s
                bandwidth_str = f"{bandwidth_bytes_per_sec / 1024:.2f} KB/s"
            else:  # B/s
                bandwidth_str = f"{bandwidth_bytes_per_sec:.2f} B/s"
                
            self.window.streaming_bandwidth_label.setText(bandwidth_str)
        except Exception as e:
            print(f"Error updating streaming bandwidth: {str(e)}")
            self.window.streaming_bandwidth_label.setText("0.00 MB/s")

    def update_on_control_change(self, control_name):
        """Update status bar based on which control changed."""
        print(f"Status bar update triggered for control: {control_name}")  # Debug print
        try:
            if control_name == "roi":
                print("Updating ROI-related status bar information")  # Debug print
                self.update_roi_data()
                self.update_image_size()
                self.update_streaming_bandwidth()
                print("ROI status bar update complete")  # Debug print
            elif control_name == "framerate":
                print("Updating framerate-related status bar information")  # Debug print
                self.update_framerate()
                self.update_streaming_bandwidth()
                print("Framerate status bar update complete")  # Debug print
            elif control_name == "exposure":
                print("Exposure changes don't affect status bar directly")  # Debug print
                # Exposure changes don't affect status bar directly
                pass
            else:
                print(f"Unknown control name: {control_name}")  # Debug print
        except Exception as e:
            print(f"Error updating status bar for {control_name}: {str(e)}")  # Debug print 
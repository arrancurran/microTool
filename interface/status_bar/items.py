"""
Specific status bar items for camera information.
"""
from typing import Any
from .status_bar_item import StatusBarItem

class CameraModelItem(StatusBarItem):
    """Status bar item for camera model name."""
    
    def format_value(self, value: str) -> str:
        return value if value else "No Camera"
        
    def get_value_from_camera(self, camera_control) -> str:
        if camera_control.camera:
            return camera_control.camera.get_device_name().decode('utf-8')
        return "No Camera"

class ROIDataItem(StatusBarItem):
    """Status bar item for ROI dimensions."""
    
    def format_value(self, value: tuple) -> str:
        if value:
            width, height = value
            return f"{width}x{height}"
        return "0x0"
        
    def get_value_from_camera(self, camera_control) -> tuple:
        width = int(camera_control.call_camera_command("width", "get"))
        height = int(camera_control.call_camera_command("height", "get"))
        return (width, height)

class FramerateItem(StatusBarItem):
    """Status bar item for camera framerate."""
    
    def format_value(self, value: float) -> str:
        return f"@ {value:.1f} Hz"
        
    def get_value_from_camera(self, camera_control) -> float:
        return float(camera_control.call_camera_command("framerate", "get"))

class ImageSizeItem(StatusBarItem):
    """Status bar item for image size."""
    
    def format_value(self, value: tuple) -> str:
        if value:
            width, height = value
            size_bytes = width * height
            print(f"ImageSizeItem: Calculating size for {width}x{height} = {size_bytes} bytes")  # Debug print

            if size_bytes >= 1024**3:  # GB
                return f"{size_bytes / (1024**3):.2f} GB"
            elif size_bytes >= 1024**2:  # MB
                return f"{size_bytes / (1024**2):.2f} MB"
            elif size_bytes >= 1024:  # KB
                return f"{size_bytes / 1024:.2f} KB"
            else:  # B
                return f"{size_bytes} B"
        return "0.00 MB"
        
    def get_value_from_camera(self, camera_control) -> tuple:
        try:
            width = int(camera_control.call_camera_command("width", "get"))
            height = int(camera_control.call_camera_command("height", "get"))
            print(f"ImageSizeItem: Got dimensions from camera: {width}x{height}")  # Debug print
            return (width, height)
        except Exception as e:
            print(f"ImageSizeItem: Error getting dimensions from camera: {str(e)}")  # Debug print
            return None

class StreamingBandwidthItem(StatusBarItem):
    """Status bar item for streaming bandwidth."""
    
    def format_value(self, value: tuple) -> str:
        if value:
            framerate, width, height = value
            bandwidth_bytes_per_sec = width * height * framerate
            if bandwidth_bytes_per_sec >= 1024**3:  # GB/s
                return f"{bandwidth_bytes_per_sec / (1024**3):.2f} GB/s"
            elif bandwidth_bytes_per_sec >= 1024**2:  # MB/s
                return f"{bandwidth_bytes_per_sec / (1024**2):.2f} MB/s"
            elif bandwidth_bytes_per_sec >= 1024:  # KB/s
                return f"{bandwidth_bytes_per_sec / 1024:.2f} KB/s"
            else:  # B/s
                return f"{bandwidth_bytes_per_sec:.2f} B/s"
        return "0.00 MB/s"
        
    def get_value_from_camera(self, camera_control) -> tuple:
        framerate = float(camera_control.call_camera_command("framerate", "get"))
        width = int(camera_control.call_camera_command("width", "get"))
        height = int(camera_control.call_camera_command("height", "get"))
        return (framerate, width, height) 
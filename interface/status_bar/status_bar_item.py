"""
Defines the abstract base class for status bar items that display camera information like model, framerate, ROI, etc.
Each item handles getting values from the camera, formatting them for display, and updating its label widget.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

class StatusBarItem(ABC):
    """Base class for all status bar items."""
    
    def __init__(self, label, update_interval: float = 0.0):

        print(f"StatusBarItem.__init__(): Initializing with update_interval={update_interval}")
        self.label = label
        self.update_interval = update_interval
        self.last_update = 0
        self._value: Optional[Any] = None
        
    @property
    def value(self) -> Any:
        """Get the current value."""
        print(f"StatusBarItem.value: Getting value: {self._value}")
        return self._value
        
    @value.setter
    def value(self, new_value: Any):
        """Set the value and update the label if needed."""
        print(f"StatusBarItem.value.setter: Setting value from {self._value} to {new_value}")
        if self._value != new_value:
            self._value = new_value
            self._update_label()
            
    def _update_label(self):
        """Update the label with the new value."""
        try:
            formatted_value = self.format_value(self._value)
            print(f"StatusBarItem.update_label: Updating label with formatted value: {formatted_value}")
            self.label.setText(formatted_value)
        except Exception as e:
            print(f"StatusBarItem.update_label: Error updating status bar label: {str(e)}")
            
    @abstractmethod
    def format_value(self, value: Any) -> str:
        """Format the value for display."""
        pass
        
    def update(self, camera_control) -> bool:
        """
        Update the value from the camera.
        
        Args:
            camera_control: The camera control object
            
        Returns:
            bool: True if the value was updated, False otherwise
        """
        print("StatusBarItem.update: Starting update from camera")
        try:
            new_value = self.get_value_from_camera(camera_control)
            print(f"StatusBarItem.update: Got new value from camera: {new_value}")
            if new_value is not None:
                self.value = new_value
                print("StatusBarItem.update: Successfully updated value")
                return True
        except Exception as e:
            print(f"StatusBarItem.update: Error updating status bar item: {str(e)}")
        print("StatusBarItem: Update failed or no new value")
        return False
        
    @abstractmethod
    def get_value_from_camera(self, camera_control) -> Any:
        """Get the value from the camera."""
        pass 
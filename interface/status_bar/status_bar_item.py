"""
Base class for status bar items.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class StatusBarItem(ABC):
    """Base class for all status bar items."""
    
    def __init__(self, label, update_interval: float = 0.0):
        """
        Initialize the status bar item.
        
        Args:
            label: The QLabel widget to update
            update_interval: How often to update in seconds (0 for on-demand only)
        """
        self.label = label
        self.update_interval = update_interval
        self.last_update = 0
        self._value: Optional[Any] = None
        
    @property
    def value(self) -> Any:
        """Get the current value."""
        return self._value
        
    @value.setter
    def value(self, new_value: Any):
        """Set the value and update the label if needed."""
        if self._value != new_value:
            self._value = new_value
            self._update_label()
            
    def _update_label(self):
        """Update the label with the current value."""
        try:
            self.label.setText(self.format_value(self._value))
        except Exception as e:
            print(f"Error updating status bar label: {str(e)}")
            
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
        try:
            new_value = self.get_value_from_camera(camera_control)
            if new_value is not None:
                self.value = new_value
                return True
        except Exception as e:
            print(f"Error updating status bar item: {str(e)}")
        return False
        
    @abstractmethod
    def get_value_from_camera(self, camera_control) -> Any:
        """Get the value from the camera."""
        pass 
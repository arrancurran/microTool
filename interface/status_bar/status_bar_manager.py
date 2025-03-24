"""
Manager for updating the status bar with camera information.
"""
from PyQt6.QtCore import QObject, QTimer
from typing import Dict, Type

from .status_bar_item import StatusBarItem
from .items import (
    CameraModelItem,
    ROIDataItem,
    FramerateItem,
    ImageSizeItem,
    StreamingBandwidthItem
)

class StatusBarManager(QObject):
    """Manages updates to the status bar with camera information."""
    
    # Register status bar items here
    STATUS_ITEMS: Dict[str, Type[StatusBarItem]] = {
        'camera_model': CameraModelItem,
        'roi_data': ROIDataItem,
        'framerate': FramerateItem,
        'image_size_on_disk': ImageSizeItem,
        'streaming_bandwidth': StreamingBandwidthItem
    }
    
    def __init__(self, window, camera_control):
        """Initialize the status bar manager."""
        super().__init__()
        self.window = window
        self.camera_control = camera_control
        self.items: Dict[str, StatusBarItem] = {}
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all)
        # TODO: We need to change this to only update when a control changes
        self.update_timer.start(200)  # Update every 200ms
        
    def initialize_items(self):
        """Initialize all registered status bar items."""
        print("Initializing status bar items...")  # Debug print
        for item_name, item_class in self.STATUS_ITEMS.items():
            print(f"Setting up {item_name} item...")  # Debug print
            try:
                # Get the label from the window
                label = getattr(self.window, f"{item_name}_label", None)
                if label is None:
                    print(f"Warning: Label for {item_name} not found")
                    continue
                    
                # Create and initialize the item
                item = item_class(label)
                self.items[item_name] = item
                print(f"Successfully initialized {item_name} item")
                
            except Exception as e:
                print(f"Error initializing {item_name} item: {str(e)}")
                
        print(f"Finished initializing items. Active items: {list(self.items.keys())}")  # Debug print
        
    def update_all(self):
        """Update all status bar items."""
        print("StatusBarManager: Starting update_all")  # Debug print
        for item_name, item in self.items.items():
            print(f"StatusBarManager: Updating {item_name}")  # Debug print
            item.update(self.camera_control)
            
    def update_on_control_change(self, control_name: str):
        """Update status bar items based on which control changed."""
        print(f"StatusBarManager: Update triggered for control: {control_name}")  # Debug print
        
        # Define which items should update for each control
        control_updates = {
            'roi': ['roi_data', 'image_size_on_disk', 'streaming_bandwidth'],
            'framerate': ['framerate', 'streaming_bandwidth'],
            'exposure': []  # Exposure changes don't affect status bar directly
        }
        
        # Update relevant items
        if control_name in control_updates:
            for item_name in control_updates[control_name]:
                if item_name in self.items:
                    print(f"StatusBarManager: Updating {item_name} for {control_name} change")  # Debug print
                    self.items[item_name].update(self.camera_control)
        else:
            print(f"StatusBarManager: Unknown control name: {control_name}")  # Debug print
            
    def cleanup(self):
        """Cleanup the status bar manager."""
        if self.update_timer:
            self.update_timer.stop()
        self.items.clear() 
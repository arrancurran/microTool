"""
Status bar utility functions for the microTool project.
Provides a centralized way to update the main window's status bar from anywhere in the project.
"""

from PyQt6.QtCore import Qt, QMetaObject, Q_ARG
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global reference to the main window
_main_window = None

def set_main_window(window):
    """
    Set the main window reference that will be used for status updates.
    This should be called once when the application starts.
    
    Args:
        window: The main QMainWindow instance of the application
    """
    global _main_window
    _main_window = window

def update_notif(message: str, duration: Optional[int] = None):
    """
    Update the status bar message in the main window.
    This function can be called from anywhere in the project to update the status bar.
    
    Args:
        message: The message to display in the status bar
        duration: Optional duration in milliseconds to show the message.
                 If None, the message will remain until the next update.
    
    Example usage:
        from utils.status import update_notif
        
        # Update status with a temporary message
        update_notif("Processing...", duration=2000)  # Shows for 2 seconds
        
        # Update status with a permanent message
        update_notif("Ready")
        
        # Update status with a progress message
        update_notif(f"Processing frame {current}/{total}")
    """
    if _main_window is None:
        logger.warning(f"Warning: Main window not set. Status message: {message}")
        return
        
    if hasattr(_main_window, 'statusBar'):
        QMetaObject.invokeMethod(
            _main_window.statusBar(),
            "showMessage",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, message),
            Q_ARG(int, duration) if duration is not None else Q_ARG(int, 0)
        )
    else:
        logger.warning(f"Warning: Main window has no status bar. Status message: {message}") 
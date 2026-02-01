from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global reference to the main window
_main_window = None

def set_main_window(window):

    global _main_window
    _main_window = window

def update_notif(message: str, duration: Optional[int] = None):
    if _main_window is None:
        logger.warning(f"Warning: Main window not set. Status message: {message}")
        return
        
    if hasattr(_main_window, 'statusBar'):
        _main_window.statusBar().showMessage(message, duration if duration is not None else 2000)

    else:
        logger.warning(f"Warning: Main window has no status bar. Status message: {message}")


def clear_notif():
    """Clear any transient status bar message.

    This leaves the permanent status bar items (camera model, ROI,
    framerate, etc.) untouched but removes the overlay text such as
    "Acquisition finished and saved to disk".
    """
    global _main_window
    if _main_window is None:
        return
    if hasattr(_main_window, "statusBar"):
        _main_window.statusBar().clearMessage()
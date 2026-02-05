from typing import Optional
import logging
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)

# Global reference to the main window and a helper that lives
# in the GUI thread to safely update the status bar from any thread.
_main_window = None
_notifier = None


class _StatusBarNotifier(QObject):
    """Helper object that proxies status-bar updates onto the GUI thread.

    All worker threads emit signals on this object; the connected slots
    run in the thread that owns the object (the main GUI thread), which
    avoids cross-thread UI access and related crashes.
    """

    showMessageRequested = pyqtSignal(str, int)
    clearMessageRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.showMessageRequested.connect(self._on_show_message)
        self.clearMessageRequested.connect(self._on_clear_message)

    @pyqtSlot(str, int)
    def _on_show_message(self, message: str, duration: int) -> None:
        global _main_window
        if _main_window is None:
            logger.warning(f"Warning: Main window not set. Status message: {message}")
            return

        if hasattr(_main_window, "statusBar"):
            _main_window.statusBar().showMessage(message, duration)
        else:
            logger.warning(
                f"Warning: Main window has no status bar. Status message: {message}"
            )

    @pyqtSlot()
    def _on_clear_message(self) -> None:
        global _main_window
        if _main_window is None:
            return
        if hasattr(_main_window, "statusBar"):
            _main_window.statusBar().clearMessage()


def set_main_window(window):
    """Register the main window and create the notifier in the GUI thread."""
    global _main_window, _notifier
    _main_window = window

    # Create the notifier once, parented to the main window so it lives
    # in the main GUI thread. All status-bar updates should go through it.
    if _notifier is None and _main_window is not None:
        _notifier = _StatusBarNotifier(parent=_main_window)


def update_notif(message: str, duration: Optional[int] = None):
    """Request a transient status-bar message.

    This is safe to call from any thread; the actual UI update is
    performed in the main GUI thread via _StatusBarNotifier.
    """
    global _notifier

    if _notifier is None:
        # set_main_window may not have been called yet.
        logger.warning(f"Warning: Notifier not initialised. Status message: {message}")
        return

    effective_duration = duration if duration is not None else 2000
    _notifier.showMessageRequested.emit(message, effective_duration)


def clear_notif():
    """Clear any transient status-bar message.

    This leaves the permanent status bar items (camera model, ROI,
    framerate, etc.) untouched but removes the overlay text such as
    "Acquisition finished and saved to disk".

    Safe to call from any thread.
    """
    global _notifier
    if _notifier is None:
        return
    _notifier.clearMessageRequested.emit()
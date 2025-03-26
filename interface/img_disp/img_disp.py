"""
Custom QLabel subclass for handling ROI drawing interactions.
Manages mouse events and painting for region of interest selection.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter

class ImgDisp(QLabel):
    """
    Custom QLabel subclass for handling ROI drawing interactions.
    Manages mouse events and painting for region of interest selection.
    
    Called by:
    - interface/ui.py: Main UI creates ImgDisp for camera display
    - interface/ui_methods.py: UIMethods handles the mouse/paint events
    
    Example usage:
        image_container = ImgDisp()
        image_container.ui_methods = ui_methods  # Connect UI methods
        image_container.setPixmap(camera_frame)  # Display camera frame
        # ROI drawing handled automatically via mouse events
    """

    #    TODO: Should we move this to ui_methods?
    def __init__(self, parent=None):
        
        """Initialize the ImgDisp"""
        super().__init__(parent)
        self.setMouseTracking(True)
        self.ui_methods = None

    def mousePressEvent(self, event):
        
        """Handle mouse press events"""
        if self.ui_methods:
            self.ui_methods.handle_mouse_press(event)

    def mouseMoveEvent(self, event):
        
        """Handle mouse move events"""
        if self.ui_methods:
            self.ui_methods.handle_mouse_move(event)

    def mouseReleaseEvent(self, event):
        
        """Handle mouse release events"""
        if self.ui_methods:
            self.ui_methods.handle_mouse_release(event)

    def paintEvent(self, event):
        
        """Handle paint events"""
        super().paintEvent(event)
        if self.ui_methods:
            painter = QPainter(self)
            self.ui_methods.handle_paint(painter)
            painter.end()

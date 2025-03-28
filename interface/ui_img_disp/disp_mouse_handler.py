from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter

""" Captures mouse events and passes to ui_methods which in turn passes to DrawROI """
class DispMouseHandler(QLabel):


    def __init__(self, parent=None):
        
        """Initialize the DispMouseHandler"""
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
        if self.ui_methods and self.ui_methods.draw_roi.current_rect:
            painter = QPainter(self)
            self.ui_methods.handle_paint(painter)
            painter.end()

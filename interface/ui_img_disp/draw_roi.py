from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPen, QColor

""" Handles all the logic for drawing the ROI on the ui image display"""

class DrawROI:
    def __init__(self):
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.current_rect = None
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.scaled_width = 0
        self.scaled_height = 0
        self.original_width = 0
        self.original_height = 0
        
        # Create the pen
        self.pen = QPen(QColor(0, 255, 0))
        self.pen.setWidth(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.start_point = self.map_to_image_coordinates(event.position())
            # Convert tuple to QPoint
            start_point = QPoint(int(self.start_point[0]), int(self.start_point[1]))
            self.current_rect = QRect(start_point, start_point)

    def mouseMoveEvent(self, event, image_label):
        if self.drawing:
            self.end_point = self.map_to_image_coordinates(event.position())
            # Convert tuples to QPoints
            start_point = QPoint(int(self.start_point[0]), int(self.start_point[1]))
            end_point = QPoint(int(self.end_point[0]), int(self.end_point[1]))
            self.current_rect = QRect(start_point, end_point).normalized()
            image_label.update()

    def mouseReleaseEvent(self, event, image_label):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.end_point = self.map_to_image_coordinates(event.position())
            # Convert tuples to QPoints
            start_point = QPoint(int(self.start_point[0]), int(self.start_point[1]))
            end_point = QPoint(int(self.end_point[0]), int(self.end_point[1]))
            self.current_rect = QRect(start_point, end_point).normalized()
            image_label.update()

    def map_to_image_coordinates(self, pos):
        # Calculate the actual position within the label
        relative_x = pos.x()
        relative_y = pos.y()
        
        # Adjust for the image offset within the container
        adjusted_x = relative_x - self.offset_x
        adjusted_y = relative_y - self.offset_y
        
        # Clamp coordinates to the image bounds
        adjusted_x = max(0, min(adjusted_x, self.scaled_width))
        adjusted_y = max(0, min(adjusted_y, self.scaled_height))
            
        # Map the position to the image coordinates using the scale factors
        image_x = int(adjusted_x / self.scale_factor_x)
        image_y = int(adjusted_y / self.scale_factor_y)

        return image_x, image_y

    def draw_rectangle(self, painter):
        """Draw the current rectangle on the image"""
        if self.current_rect:
            painter.setPen(self.pen)
            
            # Get coordinates from QPoint objects
            top_left = self.current_rect.topLeft()
            bottom_right = self.current_rect.bottomRight()
            
            # Apply scaling and offset and convert to integers
            widget_x1 = int(top_left.x() * self.scale_factor_x + self.offset_x)
            widget_y1 = int(top_left.y() * self.scale_factor_y + self.offset_y)
            widget_x2 = int(bottom_right.x() * self.scale_factor_x + self.offset_x)
            widget_y2 = int(bottom_right.y() * self.scale_factor_y + self.offset_y)
            
            # Draw the rectangle
            painter.drawRect(widget_x1, widget_y1, 
                           widget_x2 - widget_x1, 
                           widget_y2 - widget_y1)

    def update_scale_and_offset(self, scale_factor_x, scale_factor_y, offset_x, offset_y, scaled_width, scaled_height, original_width, original_height):
        """Update the scaling and offset values"""
        self.scale_factor_x = scale_factor_x
        self.scale_factor_y = scale_factor_y
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scaled_width = scaled_width
        self.scaled_height = scaled_height
        self.original_width = original_width
        self.original_height = original_height 
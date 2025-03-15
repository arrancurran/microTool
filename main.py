import sys, cv2

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint

# Import the custom modules
import utils
from interface.interface import ui_layout
from instruments.camera import Camera

# UI class that inherits from QMainWindow
class TweezerCam(ui_layout, Camera):
    def __init__(self):
        ui_layout.__init__(self)
        Camera.__init__(self)
        
        self.instruments()
        self.connect_ui_to_instruments()
        
    def instruments(self):

        self.active_camera = Camera()

    def connect_ui_to_instruments(self):
        
        # Connect the camera controls to the camera object        
        self.roi_width.valueChanged.connect(self.set_roi)
        self.roi_height.valueChanged.connect(self.set_roi)
        self.roi_offset_x.valueChanged.connect(self.set_roi)
        self.roi_offset_y.valueChanged.connect(self.set_roi)
        self.exposure_slider.valueChanged.connect(self.set_exposure)
       
        self.running = False
        self.show()

    def set_exposure(self, value):
        self.update_exposure(value)
        self.exposure_label.setText(f"Exposure: {value} µs")
        # self.send_update_status_bar(self)
        self.update_status_bar()
        
    def set_roi(self):
        roi = {
            'width': self.roi_width.value(),
            'height': self.roi_height.value(),
            'offset_x': self.roi_offset_x.value(),
            'offset_y': self.roi_offset_y.value()
        }
        self.update_roi(roi)
        # self.send_update_status_bar(self)
        self.update_status_bar()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = self.map_to_image_coordinates(event.pos())
            self.end_point = self.start_point
            self.drawing = True

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = self.map_to_image_coordinates(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_point = self.map_to_image_coordinates(event.pos())
            self.drawing = False
            self.update()

    def map_to_image_coordinates(self, pos):
        # Get the size of the displayed image
        image_container_size = self.image_container.size()
        # Calculate the size of the scaled image
        image_size = self.image_container.pixmap().size()
        
        # Calculate the scaling factor
        scale_x = self.roi_width.value() / image_size.width()
        scale_y = self.roi_height.value() / image_size.height()
        
        # Calculate the offset
        offset_x = (image_container_size.width() - image_size.width()) / 2
        offset_y = (image_container_size.height() - image_size.height()) / 2 + 32
        # TODO: Add offset for the toolbar
        
        # Adjust the position by the offset
        adjusted_x = pos.x() - offset_x
        adjusted_y = pos.y() - offset_y
        
        # Map the position to the image coordinates
        image_x = int(adjusted_x * scale_x)
        image_y = int(adjusted_y * scale_y)
        
        return QPoint(image_x, image_y)
            
    def update_image(self):
        if not self.running:
            return
        np_image_data = self.active_camera.capture_image()
        height, width = np_image_data.shape
        bytes_per_line = width
        image_data = QImage(np_image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        image = QPixmap(image_data)
        
        # Create a QPainter to draw on the QPixmap
        painter = QPainter(image)
        painter.setPen(Qt.green)  # Set the color of the square

        # Draw the square if in drawing mode
        if hasattr(self, 'start_point') and hasattr(self, 'end_point'):
            rect = QRect(self.start_point, self.end_point)
            painter.drawRect(rect)
        
        painter.end()
        
        # Scale image to fit the image_container while maintaining aspect ratio
        image_container_size = self.image_container.size()
        scaled_image = image.scaled(image_container_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_container.setPixmap(scaled_image)
        
        utils.calc_img_hist(self, np_image_data)
        QTimer.singleShot(20, self.update_image)
        
    def start_live_display(self):
        try:
            self.start_cam()
            self.update_image()
        except Exception as e:
            print(f"Camera start error: {e}")
            return
        self.running = True
        self.update_image()

    def stop_live_display(self):
        if self.running:
            self.running = False
            self.stop_cam()

    def start_recording(self):
        print(f"Recording started")
    
    def keyPressEvent(self, event):
        if  event.key() == Qt.Key.Key_Escape:  # Handle the Escape key
            self.running = False
            self.stop_cam()
            self.close()
            cv2.destroyAllWindows()
            print("Escape key pressed")
            self.close()

    def closeEvent(self, event):
        # Stop the camera and clean up
        self.running = False
        self.stop_cam()
        self.close()
        cv2.destroyAllWindows()
        print("Window closed")
        super().closeEvent(event)
            
        event.accept()  # Let the window close

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TweezerCam()
    sys.exit(app.exec())

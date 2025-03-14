import sys, cv2

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer

import utils
from interface.interface import ui_layout
from instruments.camera import Camera

# UI class that inherits from QMainWindow
class ColloidCamUI(ui_layout):
    def __init__(self):
        ui_layout.__init__(self)
        
        self.instruments()
        self.setupUI()
        
    def instruments(self):
        # init cam and get cam_meta
        self.active_camera = Camera()

    def setupUI(self):
        
        # Connect the camera controls to the camera object        
        self.roi_width.valueChanged.connect(self.update_roi)
        self.roi_height.valueChanged.connect(self.update_roi)
        self.roi_offset_x.valueChanged.connect(self.update_roi)
        self.roi_offset_y.valueChanged.connect(self.update_roi)
        self.exposure_slider.valueChanged.connect(self.set_exposure)
       
        self.running = False
        self.show()

    def set_exposure(self, value):
        self.active_camera.set_exposure(value)
        self.exposure_label.setText(f"Exposure: {value} µs")
        
    def update_roi(self):
        roi = {
            'width': self.roi_width.value(),
            'height': self.roi_height.value(),
            'offset_x': self.roi_offset_x.value(),
            'offset_y': self.roi_offset_y.value()
        }
        self.active_camera.update_roi(roi)

    def update_image(self):
        if not self.running:
            return
        image_data = self.active_camera.capture_image()
        height, width = image_data.shape
        bytes_per_line = width
        formated_image = QImage(image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap(formated_image)
        # Scale image to fit the view while maintaining aspect ratio
        view_size = self.view.size()
        scaled_pixmap = pixmap.scaled(
            view_size, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.view.setPixmap(scaled_pixmap)
        utils.calc_img_hist(self, image_data)
        QTimer.singleShot(20, self.update_image)
        
    def start_live_display(self):
  
        try:
            self.active_camera.start_cam()
            self.update_image() # Attempt to start the camera
        except Exception as e:
            print(f"Camera start error: {e}")
            return
        self.running = True
        self.update_image()

    def stop_live_display(self):
        if self.running:
            self.running = False
            self.active_camera.stop_cam()

    def start_recording(self):
        print(f"Recording started")
    
    def keyPressEvent(self, event):
        if  event.key() == Qt.Key.Key_Escape:  # Handle the Escape key
            self.running = False
            self.active_camera.stop_cam()
            self.active_camera.close()
            cv2.destroyAllWindows()
            print("Escape key pressed")
            self.close()  # Closes the window and triggers closeEvent

    def closeEvent(self, event):
        # Stop the camera and clean up
        self.running = False
        self.active_camera.stop_cam()
        self.active_camera.close()
        cv2.destroyAllWindows()
        print("Window closed")
        super().closeEvent(event)
            
        event.accept()  # Let the window close

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ColloidCamUI()
    sys.exit(app.exec())

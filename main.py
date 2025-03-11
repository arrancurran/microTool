import sys, cv2, matplotlib.pyplot as plt

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import utils

from instruments.camera import Camera

class xiCam(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.instruments()
        
        self.initUI()

    def instruments(self):
        
        # init cam and get metadata
        self.active_camera = Camera()
        self.active_camera.start_cam()
        self.metadata = self.active_camera.get_cam_metadata()
        
    def initUI(self):
        
        self.setWindowTitle('xiCam')
        self.showMaximized()
        self.setStyleSheet("background-color: #25292E;") 
        
        # Creates the central widget, which will contain all other UI elements.
        xiCam_widget = QWidget(self)
        
        # Tells PyQt to use this widget as the main container for other layouts and widgets.
        self.setCentralWidget(xiCam_widget)
        # A horizontal layout — meaning child elements will be arranged side-by-side.
        xiCam_layout = QHBoxLayout(xiCam_widget)
        
        xiCam_ctrls_widget = QWidget(self)
        xiCam_ctrls_layout = QGridLayout(xiCam_ctrls_widget)
        
        self.hist_display = FigureCanvas(plt.figure())
        # self.hist_display.setFixedSize(500, 100)
        
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal, self)
        
        self.exposure_slider.setStyleSheet("background-color: #FFFFFF;")
        self.exposure_slider.setRange(self.metadata['min_exposure'], self.metadata['max_exposure'])
        self.exposure_slider.setValue(self.metadata['min_exposure'])
        self.exposure_slider.setTickInterval((self.metadata['max_exposure'] - self.metadata['min_exposure']) // 10)
        self.exposure_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.exposure_slider.valueChanged.connect(self.set_exposure)
        
        self.exposure_label = QLabel(self)
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.update_exposure_label(self.metadata['min_exposure'])

        xiCam_ctrls_layout.addWidget(self.hist_display, 0, 1)
        xiCam_ctrls_layout.addWidget(self.exposure_slider, 0, 2)
        xiCam_ctrls_layout.addWidget(self.exposure_label, 1, 2)
        
        self.cam_display = QLabel(self)
        self.cam_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        xiCam_layout.addWidget(xiCam_ctrls_widget, 1)
        xiCam_layout.addWidget(self.cam_display, 2)

        self.show()
        self.running = True
        
        self.update_image()
        
        print(f"Camera model: { self.exposure_slider.width()}")

    def set_exposure(self, value):
        self.active_camera.set_exposure(value)
        self.update_exposure_label(value)

    def update_exposure_label(self, value):
        self.exposure_label.setText(f"Exposure: {value} µs")

    def update_image(self):
        if self.running:
            
            img_data = self.active_camera.capture_image()
            
            if len(img_data.shape) == 2:
                height, width = img_data.shape
                bytes_per_line = width
                q_img = QImage(img_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            else:
                img_data = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)
                height, width, channel = img_data.shape
                bytes_per_line = 3 * width
                q_img = QImage(img_data.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(q_img)
            self.cam_display.setPixmap(pixmap.scaled(self.cam_display.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
            utils.calc_img_hist(self,img_data)

            QTimer.singleShot(20, self.update_image)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Q:
            self.running = False
            self.active_camera.stop_cam()
            self.active_camera.close()
            cv2.destroyAllWindows()
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = xiCam()
    sys.exit(app.exec())

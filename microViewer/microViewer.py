import sys
import h5py
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QSlider, QFileDialog, QLabel, QHBoxLayout, QSpinBox
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from scipy.ndimage import center_of_mass

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("H5 Image Viewer with ROI")

        self.data = None
        self.current_frame = 0
        self.roi = None

        self.com_plot = pg.PlotWidget(title="Center of Mass (x, y)")
        self.com_plot.addLegend()
        self.com_x_curve = self.com_plot.plot(pen='r', name='X')
        self.com_y_curve = self.com_plot.plot(pen='b', name='Y')
        self.hist_plot = pg.ImageView()
        self.hist_plot.ui.histogram.hide()
        self.hist_plot.ui.roiBtn.hide()
        self.hist_plot.ui.menuBtn.hide()
        
        self.bin_spinner = QSpinBox()
        self.bin_spinner.setRange(10, 500)
        self.bin_spinner.setValue(100)
        self.bin_spinner.valueChanged.connect(self.compute_histogram)
        
        self.hist1d_plot = pg.PlotWidget(title="1D Histograms of COM (X, Y)")
        self.hist1d_plot.addLegend()
        self.hist1d_plot.setLabel('bottom', 'Position')
        self.hist1d_plot.setLabel('left', 'Counts')
        self.hist1d_x = self.hist1d_plot.plot(pen=None, symbol='o', symbolBrush='r', name='X')
        self.hist1d_y = self.hist1d_plot.plot(pen=None, symbol='x', symbolBrush='b', name='Y')

        self.init_ui()

    def init_ui(self):
        self.image_view = pg.ImageView()
        self.image_view.ui.histogram.hide()
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(0)
        self.threshold_slider.valueChanged.connect(self.update_image)
        
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setEnabled(False)
        self.frame_slider.valueChanged.connect(self.change_frame)
        
        self.load_button = QPushButton("Load H5 File")
        self.load_button.clicked.connect(self.load_file)

        self.roi_button = QPushButton("Crop to ROI")
        self.roi_button.clicked.connect(self.crop_to_roi)
        
        self.com_button = QPushButton("Compute Center of Mass")
        self.com_button.clicked.connect(self.compute_com)

        self.label = QLabel("Threshold")

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.load_button)
        top_bar.addWidget(self.label)
        top_bar.addWidget(self.threshold_slider)
        top_bar.addWidget(self.roi_button)
        top_bar.addWidget(self.com_button)
        
        top_bar.addWidget(QLabel("Bins:"))
        top_bar.addWidget(self.bin_spinner)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.image_view)
        
        layout.addWidget(self.image_view)
        layout.addWidget(self.frame_slider)
        
        layout.addWidget(self.com_plot)
        
        layout.addWidget(self.hist_plot)
        
        layout.addWidget(self.hist1d_plot)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open H5 File", "", "HDF5 Files (*.h5 *.hdf5)")
        if not path:
            return

        with h5py.File(path, 'r') as f:
            self.data = f[list(f.keys())[0]][:]

        # self.compute_com()
        self.frame_slider.setMaximum(self.data.shape[0] - 1)
        self.frame_slider.setEnabled(True)
        self.frame_slider.setValue(0)
        self.show_image()

        if self.roi is None:
            self.roi = pg.RectROI([10, 10], [100, 100], pen='r')
            self.image_view.addItem(self.roi)

    
    def compute_com(self):
        if self.data is None:
            return
        frames = self.data.shape[0]
        coms = np.array([
            center_of_mass(self.data[i]) for i in range(frames)
        ])
        # Center COMs by subtracting the mean
        mean_com = np.mean(coms, axis=0)
        self.coms = coms - mean_com
        self.com_x_curve.setData(self.coms[:, 1], pen='r')  # x is column index
        self.com_y_curve.setData(self.coms[:, 0], pen='b')  # y is row index
        
        self.compute_histogram()
        

    def compute_histogram(self):
        if not hasattr(self, 'coms'):
            return

        bins = self.bin_spinner.value()
        x = self.coms[:, 1]  # x = column index
        y = self.coms[:, 0]  # y = row index

        # 2D histogram
        H2D, xedges, yedges = np.histogram2d(x, y, bins=bins)
        self.hist_plot.setImage(H2D.T, autoLevels=True)

        # 1D histograms
        hx, xbins = np.histogram(x, bins=bins)
        hy, ybins = np.histogram(y, bins=bins)

        # Use bin centers for plotting
        xcenters = 0.5 * (xbins[:-1] + xbins[1:])
        ycenters = 0.5 * (ybins[:-1] + ybins[1:])

        self.hist1d_x.setData(xcenters, hx)
        self.hist1d_y.setData(ycenters, hy)
    
    def show_image(self):
        if self.data is not None:
            frame = self.data[self.current_frame]
            self.image_view.setImage(self.apply_threshold(frame), autoLevels=True)

    def update_image(self):
        self.show_image()

    def change_frame(self, value):
        self.current_frame = value
        self.show_image()
    
    def apply_threshold(self, frame):
        t = self.threshold_slider.value()
        thresholded = frame.copy()
        thresholded[thresholded < t] = 0
        return thresholded

    def crop_to_roi(self):
        if self.data is None or self.roi is None:
            return

        x, y = self.roi.pos()
        w, h = self.roi.size()

        x, y, w, h = map(int, [x, y, w, h])
        self.data = self.data[:, y:y + h, x:x + w]
        self.current_frame = 0
        self.image_view.removeItem(self.roi)
        self.roi = None
        self.show_image()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.resize(800, 600)
    viewer.show()
    sys.exit(app.exec())
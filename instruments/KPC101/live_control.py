"""Compact live piezo control suitable for embedding in microTool."""

from concurrent.futures import ThreadPoolExecutor
import time

from PyQt6.QtCore import Qt, QTimer, QSignalBlocker
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QDoubleSpinBox, QSlider, QApplication,
)

from .controller import KPC101, Mode


class PiezoControl(QWidget):
    """Live targets are coalesced, with at most one device call in flight.

    No device is opened or enabled automatically. Status polling never
    disables controls and cannot replace a target being edited by the user.
    """

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller or KPC101()
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Piezo")
        self._future = None
        self._queued = None
        self._target = None
        self._status = None
        self._closed = False
        self._reserved = False
        self._next_poll = 0
        self._initial_target = True
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel("Piezo"))
        self.serial = QComboBox()
        self.serial.setEditable(True)
        self.serial.setPlaceholderText("KPC101 serial")
        row.addWidget(self.serial)
        self.find_button = QPushButton("Find")
        self.find_button.clicked.connect(lambda: self._start(self.controller.discover, self._devices))
        row.addWidget(self.find_button)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect)
        row.addWidget(self.connect_button)
        self.enable_button = QPushButton("Enable")
        self.enable_button.clicked.connect(self._enable)
        row.addWidget(self.enable_button)
        self.mode = QComboBox()
        for mode in Mode:
            self.mode.addItem(mode.name.replace("_", " ").title(), mode)
        self.mode.activated.connect(self._mode_changed)
        row.addWidget(self.mode)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.numeric = QDoubleSpinBox()
        self.numeric.setDecimals(2)
        self.numeric.setSingleStep(0.1)
        self.numeric.setKeyboardTracking(False)
        self.numeric.setSuffix(" V")
        self.numeric.setRange(0, 75)
        self.slider.setRange(0, 7500)
        self.slider.valueChanged.connect(lambda value: self._changed(value / 100))
        self.numeric.valueChanged.connect(self._changed)
        row.addWidget(self.slider)
        row.addWidget(self.numeric)
        layout.addLayout(row)
        self.readback = QLabel("Disconnected — connect a KPC101 to control the piezo")
        self.readback.setWordWrap(True)
        layout.addWidget(self.readback)
        self.setToolTip("Open loop: volts. Closed loop: percent of calibrated travel. Disconnect leaves output unchanged.")
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        QApplication.instance().aboutToQuit.connect(self.shutdown)
        self._buttons()

    def _start(self, action, callback=None, *, background=False):
        if self._closed or self._reserved:
            return False
        if self._future is not None:
            if not background and self._future[2] and self._queued is None:
                self._queued = (action, callback)
                self._buttons()
                return True
            return False
        self._future = (self._worker.submit(action), callback, background)
        self._buttons()
        return True

    def _devices(self, serials):
        self.serial.clear()
        self.serial.addItems(serials)
        if serials:
            self.serial.setCurrentIndex(0)
        self.readback.setText(f"Found {len(serials)} KPC101 device(s). Select one and connect.")

    def _connect(self):
        self._target = None
        if self.controller.serial is not None:
            self._start(self.controller.disconnect, self._disconnected)
        else:
            serial = self.serial.currentText().strip()
            self._initial_target = True
            self._start(lambda: self.controller.connect(serial), self._display)

    def _disconnected(self, _):
        self._status = None
        self.readback.setText("Disconnected; output left unchanged.")

    def _enable(self):
        enabled = not self._status.enabled
        self._target = None
        self._start(lambda: self.controller.enable(enabled), self._refresh)

    def _mode_changed(self, _):
        mode = self.mode.currentData()
        self._target = None
        self._initial_target = True
        self._start(lambda: self.controller.set_mode(mode), self._refresh)

    def _refresh(self, _):
        self._next_poll = 0

    def _changed(self, value):
        with QSignalBlocker(self.numeric), QSignalBlocker(self.slider):
            self.numeric.setValue(value)
            self.slider.setValue(round(value * 100))
        if self._status and self.slider.isEnabled():
            self._target = (self._status.mode, self.numeric.value())

    def _buttons(self):
        connected = self.controller.serial is not None
        busy = self._queued is not None or (self._future is not None and not self._future[2])
        self.find_button.setEnabled(not connected and not busy)
        self.serial.setEnabled(not connected and not busy)
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.connect_button.setEnabled(not busy)
        status = self._status
        self.enable_button.setEnabled(connected and status is not None and not busy)
        self.enable_button.setText("Disable" if status and status.enabled else "Enable")
        self.mode.setEnabled(connected and status is not None and not busy)
        ready = bool(connected and status and status.enabled and not status.zeroing and not status.error
                     and (not status.mode.closed_loop or status.feedback_connected) and not busy)
        self.slider.setEnabled(ready)
        self.numeric.setEnabled(ready)

    def _display(self, status):
        previous = self._status
        self._status = status
        closed = status.mode.closed_loop
        maximum = 100 if closed else status.max_voltage
        with QSignalBlocker(self.numeric), QSignalBlocker(self.slider), QSignalBlocker(self.mode):
            self.mode.setCurrentIndex(self.mode.findData(status.mode))
            self.numeric.setSuffix(" % travel" if closed else " V")
            self.numeric.setMaximum(maximum)
            self.slider.setMaximum(round(maximum * 100))
            if self._initial_target or previous is None or previous.mode != status.mode:
                value = status.position_percent if closed else status.voltage
                self.numeric.setValue(value)
                self.slider.setValue(round(value * 100))
                self._initial_target = False
        actual = f"{status.position_percent:.2f}% travel" if closed else f"{status.voltage:.2f} V"
        self.readback.setText(f"Piezo: {actual} | {'Enabled' if status.enabled else 'Disabled'}"
                              + (" | Zeroing" if status.zeroing else "")
                              + (" | Device error" if status.error else ""))

    def _tick(self):
        if self._closed or self._reserved:
            return
        if self._future:
            future, callback, _ = self._future
            if not future.done():
                return
            self._future = None
            try:
                result = future.result()
                if callback:
                    callback(result)
            except Exception as exc:
                self._target = None
                self._status = None
                self.readback.setText(f"Piezo: {exc}")
                self._next_poll = time.monotonic() + 2
            self._buttons()
        if self._queued is not None:
            action, callback = self._queued
            self._queued = None
            self._start(action, callback)
        elif self._target is not None:
            mode, value = self._target
            self._target = None
            action = self.controller.set_position_percent if mode.closed_loop else self.controller.set_voltage
            self._start(lambda: action(value), background=True)
        elif self.controller.serial is not None and time.monotonic() >= self._next_poll:
            self._next_poll = time.monotonic() + 0.5
            self._start(self.controller.status, self._display, background=True)

    def reserve_for_scan(self):
        """Suspend manual control; return a barrier for already-running device work."""
        if self._closed or self._reserved:
            raise RuntimeError("Piezo is unavailable or already scanning.")
        self._reserved = True
        self._target = self._queued = None
        self.setEnabled(False)
        return self._worker.submit(lambda: None)

    def release_from_scan(self):
        self._reserved = False
        self._initial_target = True
        self._next_poll = 0
        self.setEnabled(True)

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        self.timer.stop()
        self._target = None
        self._queued = None
        self._worker.submit(self.controller.disconnect)
        self._worker.shutdown(wait=True)

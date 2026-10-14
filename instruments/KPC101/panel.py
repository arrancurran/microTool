"""Embeddable PyQt6 control panel. All hardware calls use one worker thread."""

from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QDoubleSpinBox, QMessageBox,
)

from .controller import KPC101, Mode


class KPC101Panel(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller or KPC101()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="KPC101")
        self._pending = None
        self._poll = None
        self._closed = False
        self._last = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("KPC101 piezo controller" + (" — SIMULATION" if self.controller.simulate else "")))
        row = QHBoxLayout()
        self.serial = QComboBox()
        self.serial.setEditable(True)
        row.addWidget(self.serial)
        self.scan = QPushButton("Find devices")
        self.scan.clicked.connect(lambda: self._submit(self.controller.discover, self._devices))
        row.addWidget(self.scan)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect)
        row.addWidget(self.connect_button)
        layout.addLayout(row)
        self.controls = QWidget()
        control_layout = QVBoxLayout(self.controls)
        row = QHBoxLayout()
        for title, action in (("Enable output", lambda: self.controller.enable(True)),
                              ("Disable output", lambda: self.controller.enable(False)),
                              ("Identify", self.controller.identify), ("Zero reference", self._zero)):
            button = QPushButton(title)
            if title == "Zero reference":
                button.clicked.connect(self._zero)
            else:
                button.clicked.connect(lambda checked=False, fn=action: self._submit(fn))
            row.addWidget(button)
        control_layout.addLayout(row)
        row = QHBoxLayout()
        self.mode = QComboBox()
        for mode in Mode:
            self.mode.addItem(mode.name.replace("_", " ").title(), mode)
        row.addWidget(self.mode)
        button = QPushButton("Apply mode")
        button.clicked.connect(self._set_mode)
        row.addWidget(button)
        control_layout.addLayout(row)
        row = QHBoxLayout()
        self.voltage = QDoubleSpinBox()
        self.voltage.setDecimals(3)
        self.voltage.setSuffix(" V")
        self.voltage.setRange(0, 75)
        row.addWidget(self.voltage)
        self.apply_voltage = QPushButton("Set voltage")
        self.apply_voltage.clicked.connect(lambda: self._set_voltage())
        row.addWidget(self.apply_voltage)
        self.position = QDoubleSpinBox()
        self.position.setDecimals(3)
        self.position.setRange(0, 100)
        self.position.setSuffix(" % travel")
        row.addWidget(self.position)
        self.apply_position = QPushButton("Set position")
        self.apply_position.clicked.connect(lambda: self._set_position())
        row.addWidget(self.apply_position)
        control_layout.addLayout(row)
        layout.addWidget(self.controls)
        self.readback = QLabel("Disconnected")
        self.readback.setWordWrap(True)
        layout.addWidget(self.readback)
        self.message = QLabel("Connection does not enable output. Disconnect leaves output unchanged.")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self._buttons()

    def _devices(self, serials):
        self.serial.clear()
        self.serial.addItems(serials)
        self.message.setText(f"Found {len(serials)} KPC101 device(s).")

    def _connect(self):
        if self.controller.serial is None:
            serial = self.serial.currentText()
            self._submit(lambda: self.controller.connect(serial), self._display)
        else:
            self._submit(self.controller.disconnect, lambda _: self.readback.setText("Disconnected; output left unchanged."))

    def _set_voltage(self):
        value = self.voltage.value()
        self._submit(lambda: self.controller.set_voltage(value))

    def _set_mode(self):
        mode = self.mode.currentData()
        self._submit(lambda: self.controller.set_mode(mode))

    def _set_position(self):
        value = self.position.value()
        self._submit(lambda: self.controller.set_position_percent(value))

    def _zero(self):
        if QMessageBox.question(self, "Zero reference", "Start strain-gauge reference zeroing? This can move the actuator and takes about 10 seconds.") == QMessageBox.StandardButton.Yes:
            self._submit(self.controller.zero)

    def _submit(self, function, callback=None):
        if self._pending is not None or self._closed:
            return
        self._pending = (self._executor.submit(function), callback)
        self._buttons()

    def _buttons(self):
        busy = self._pending is not None
        connected = self.controller.serial is not None
        self.scan.setEnabled(not busy and not connected)
        self.serial.setEnabled(not busy and not connected)
        self.connect_button.setEnabled(not busy)
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.controls.setEnabled(connected and not busy)
        status = self._last
        ready = connected and status is not None and status.enabled and not status.zeroing and not status.error
        self.apply_voltage.setEnabled(bool(ready and not status.mode.closed_loop))
        self.apply_position.setEnabled(bool(ready and status.mode.closed_loop and status.feedback_connected))

    def _display(self, status):
        self._last = status
        self.voltage.setMaximum(status.max_voltage)
        position = "n/a" if status.position_percent is None else f"{status.position_percent:.3f}%"
        self.readback.setText(
            f"{status.serial} | {status.mode.name} | Output {'enabled' if status.enabled else 'disabled'}\n"
            f"Voltage: {status.voltage:.3f} / {status.max_voltage:g} V | Position: {position}\n"
            f"Feedback: {status.feedback_connected} | Zeroed: {status.zeroed} | Zeroing: {status.zeroing} | Error: {status.error}"
        )

    def _tick(self):
        # Readback shares the worker queue, but must not make the UI busy.
        # Commands clicked during a read queue behind it instead of being lost.
        if self._poll is not None and self._poll.done():
            future = self._poll
            self._poll = None
            try:
                status = future.result()
                if self.controller.serial == status.serial:
                    self._display(status)
            except Exception as exc:
                self._last = None
                self.message.setText(str(exc))
            self._buttons()
        if self._pending:
            future, callback = self._pending
            if not future.done():
                return
            self._pending = None
            try:
                result = future.result()
                if callback:
                    callback(result)
            except Exception as exc:
                self._last = None
                self.message.setText(str(exc))
            self._buttons()
            return
        if self.controller.serial is not None and self._poll is None and not self._closed:
            self._poll = self._executor.submit(self.controller.status)

    def shutdown(self):
        """Call when removing an embedded panel or closing the host window."""
        if self._closed:
            return
        self._closed = True
        self.timer.stop()
        self._executor.submit(self.controller.disconnect)
        self._executor.shutdown(wait=True)

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

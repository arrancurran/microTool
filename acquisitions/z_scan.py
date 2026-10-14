"""Sequential piezo moves and fresh camera frames, with aligned HDF5 Z metadata."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
import math
from pathlib import Path
import threading
import time

import h5py
import numpy as np
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


def scan_positions(start, end, increment):
    """Include both endpoints, using a shorter final step when necessary."""
    if not all(math.isfinite(v) for v in (start, end, increment)) or increment <= 0:
        raise ValueError("Z increment must be positive and all Z values finite.")
    a, b, step = map(lambda v: Decimal(str(v)), (start, end, increment))
    count = int(abs(b - a) // step)
    if count > 100000:
        raise ValueError("Scan exceeds 100,001 planes. Increase the increment.")
    direction = 1 if b >= a else -1
    values = [float(a + direction * step * i) for i in range(count + 1)]
    if values[-1] != float(b):
        values.append(float(b))
    return values


def acquire_stack(camera, piezo, positions, base_path, settle, stop, progress=lambda *_: None,
                  metadata=None, spots=None):
    """Run off the GUI thread, with exclusive ownership of camera and piezo.

    Camera acquisition is restarted at each settled plane to avoid pre-move
    buffered frames. Partial files remain readable on cancellation or failure.
    """
    status = piezo.status()
    if not status.enabled or status.zeroing or status.error:
        raise RuntimeError("Connect and enable the piezo; resolve zeroing/device errors first.")
    mode = status.mode
    closed = mode.closed_loop
    limit = 100 if closed else status.max_voltage
    if closed and not status.feedback_connected:
        raise RuntimeError("Closed-loop Z scan requires strain-gauge feedback.")
    if not positions or any(not math.isfinite(z) or z < 0 or z > limit for z in positions):
        raise ValueError(f"Z values must be between 0 and {limit} {'% travel' if closed else 'V'}.")
    filename = f"{base_path}_zscan_{datetime.now():%Y%m%d_%H%M%S_%f}.h5"
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    units = "percent_travel" if closed else "V"
    move = piezo.set_position_percent if closed else piezo.set_voltage
    with h5py.File(filename, "x") as file:
        file.attrs.update({k: v for k, v in (metadata or {}).items() if v is not None})
        file.attrs.update({"Acquisition Type": "Z Scan", "Piezo Serial": status.serial,
                           "Piezo Mode": mode.name, "Z Units": units, "Settle Time": settle,
                           "Requested Frames": len(positions), "Acquired Frames": 0,
                           "Scan Status": "running", "Start Time": datetime.now().isoformat()})
        planned = file.create_dataset("z_requested", data=positions)
        planned.attrs["units"] = units
        z_data = file.create_dataset("z_positions", (0,), maxshape=(None,), dtype="f8")
        actual_data = file.create_dataset("z_readback", (0,), maxshape=(None,), dtype="f8")
        for dataset in (z_data, actual_data):
            dataset.attrs["units"] = units
        z_data.attrs["description"] = "Commanded Z for each saved frame"
        actual_data.attrs["description"] = "Piezo readback immediately before each exposure; volts in open loop"
        timestamps = file.create_dataset("timestamps", (0,), maxshape=(None,), dtype="f8")
        timestamps.attrs["units"] = "seconds since Unix epoch (host capture time)"
        fields = ("x", "y", "z", "intensity", "vortex", "phase")
        trap_data = np.zeros(len(spots or []), dtype=[(f, "f8") for f in fields])
        for i, spot in enumerate(spots or []):
            for field in fields:
                trap_data[i][field] = spot.get(field, 1 if field == "intensity" else 0)
        file.create_dataset("optical traps", data=trap_data)
        frames = None
        saved = 0
        try:
            for target in positions:
                if stop.is_set():
                    break
                move(target)
                if stop.wait(settle):
                    break
                deadline = time.monotonic() + 5
                while True:
                    current = piezo.status()
                    if current.mode != mode or not current.enabled or current.error or current.zeroing:
                        raise RuntimeError("Piezo state changed during the scan.")
                    if closed and not current.feedback_connected:
                        raise RuntimeError("Piezo feedback was disconnected.")
                    actual = current.position_percent if closed else current.voltage
                    tolerance = 0.1 if closed else max(0.02, limit / 32767 * 2)
                    if abs(actual - target) <= tolerance:
                        break
                    if time.monotonic() > deadline:
                        raise TimeoutError(f"Piezo did not reach Z={target}; readback={actual}.")
                    if stop.wait(0.05):
                        break
                if stop.is_set():
                    break
                camera.start_camera()
                try:
                    deadline = time.monotonic() + 5
                    while camera.get_image() is False:
                        if stop.wait(0.01):
                            break
                        if time.monotonic() > deadline:
                            raise TimeoutError("Camera did not deliver a fresh frame.")
                    if stop.is_set():
                        break
                    data = camera.get_image_data()
                    if data is None:
                        raise RuntimeError("Camera returned no image.")
                    image = np.array(data, copy=True)
                    timestamp = time.time()
                finally:
                    camera.stop_camera()
                if frames is None:
                    frames = file.create_dataset("frames", (0,) + image.shape,
                                                 maxshape=(None,) + image.shape, dtype=image.dtype, chunks=True)
                if image.shape != frames.shape[1:]:
                    raise RuntimeError("Camera frame shape changed during scan.")
                try:
                    for dataset in (frames, z_data, actual_data, timestamps):
                        dataset.resize(saved + 1, axis=0)
                    frames[saved], z_data[saved], actual_data[saved], timestamps[saved] = image, target, actual, timestamp
                except Exception:
                    for dataset in (frames, z_data, actual_data, timestamps):
                        dataset.resize(saved, axis=0)
                    raise
                saved += 1
                file.attrs["Acquired Frames"] = saved
                file.flush()
                progress(saved, len(positions))
            file.attrs["Scan Status"] = "cancelled" if stop.is_set() else "complete"
        except Exception as exc:
            file.attrs["Scan Status"] = "failed"
            file.attrs["Error"] = str(exc)
            raise RuntimeError(f"{exc} Partial scan saved to {filename}") from exc
        finally:
            file.attrs["End Time"] = datetime.now().isoformat()
    return filename, saved


class ZScan(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)

    def __init__(self, window, stream):
        super().__init__(window)
        self.window, self.stream = window, stream
        self.is_running = False
        self._future = None
        self._stop = threading.Event()
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ZScan")
        self._was_streaming = False
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._check)

    def start(self, base_path, positions, settle, metadata):
        panel = self.window.piezo_control
        barrier = panel.reserve_for_scan()
        try:
            self._was_streaming = bool(self.stream.live_stream_qthread and self.stream.live_stream_qthread.isRunning())
            self.stream.stop_stream()
            self._stop.clear()
            spots = [dict(spot) for spot in getattr(self.window, "optical_traps", [])]
            def run():
                barrier.result()
                return acquire_stack(self.stream.camera_control, panel.controller, positions,
                                     base_path, settle, self._stop, self.progress.emit, metadata, spots)
            self._future = self._worker.submit(run)
            self.is_running = True
            self.timer.start()
        except Exception:
            panel.release_from_scan()
            if self._was_streaming:
                self.stream.start_stream()
            raise

    def stop(self):
        self._stop.set()

    def _check(self):
        if self._future is None or not self._future.done():
            return
        try:
            filename, count = self._future.result()
            message = f"{'Stopped' if self._stop.is_set() else 'Complete'}: {count} images saved to {filename}"
        except Exception as exc:
            message = str(exc)
        self._future = None
        self.is_running = False
        self.timer.stop()
        self.window.piezo_control.release_from_scan()
        if self._was_streaming:
            try:
                self.stream.start_stream()
            except Exception as exc:
                message += f" Live view could not restart: {exc}"
        self.finished.emit(message)

    def shutdown(self):
        self.stop()
        self.timer.stop()
        self._worker.shutdown(wait=True)

"""Thorlabs KPC101 native Kinesis API, independent of any UI framework."""

import ctypes as C
from dataclasses import dataclass
from enum import IntEnum
import math
import os
from pathlib import Path
import threading
import time


class KPCError(RuntimeError):
    """Connection, device, or state error."""


class Mode(IntEnum):
    OPEN_LOOP = 1
    CLOSED_LOOP = 2
    OPEN_LOOP_SMOOTHED = 3
    CLOSED_LOOP_SMOOTHED = 4

    @property
    def closed_loop(self):
        return self in (Mode.CLOSED_LOOP, Mode.CLOSED_LOOP_SMOOTHED)


@dataclass(frozen=True)
class Status:
    serial: str
    mode: Mode
    voltage: float
    max_voltage: float
    position_percent: float | None
    enabled: bool
    feedback_connected: bool
    zeroed: bool
    zeroing: bool
    error: bool
    bits: int


class KPC101:
    """One controller. Calls are serialized; use a worker thread in GUI clients.

    Position uses percent of configured travel (0..100), avoiding assumptions
    about the attached actuator's travel/calibration. Disconnect leaves output
    unchanged. Connection never enables output or changes control mode.
    """

    def __init__(self, kinesis_path=None, *, simulate=False):
        self.path = Path(kinesis_path or os.environ.get(
            "THORLABS_KINESIS_PATH", r"C:\Program Files\Thorlabs\Kinesis"))
        self.simulate = simulate
        self.serial = None
        self._dll = None
        self._dll_dir = None
        self._lock = threading.RLock()
        self._mode = Mode.OPEN_LOOP
        self._voltage = self._position = 0.0
        self._enabled = self._zeroed = False
        self._zero_until = 0.0

    def _load(self):
        if self._dll is not None:
            return
        if os.name != "nt":
            raise KPCError("Hardware control requires Windows and Thorlabs Kinesis.")
        try:
            self._dll_dir = os.add_dll_directory(str(self.path))
            dll = C.CDLL(str(self.path / "Thorlabs.MotionControl.KCube.PiezoStrainGauge.dll"))
            signatures = {
                "TLI_BuildDeviceList": (C.c_short, []),
                "TLI_GetDeviceListByTypeExt": (C.c_short, [C.c_char_p, C.c_uint32, C.c_int]),
            }
            for name in ("Open", "Enable", "Disable", "RequestStatus", "RequestOutputVoltage"):
                signatures["KPC_" + name] = (C.c_short, [C.c_char_p])
            for name in ("Close", "StopPolling", "Identify"):
                signatures["KPC_" + name] = (None, [C.c_char_p])
            for name in ("LoadSettings", "CheckConnection", "SetZero", "RequestMaxOutputVoltage", "RequestPositionControlMode"):
                signatures["KPC_" + name] = (C.c_bool, [C.c_char_p])
            signatures["KPC_StartPolling"] = (C.c_bool, [C.c_char_p, C.c_int])
            for name in ("GetOutputVoltage", "GetMaxOutputVoltage", "GetPositionControlMode"):
                signatures["KPC_" + name] = (C.c_short, [C.c_char_p])
            signatures["KPC_GetPosition"] = (C.c_uint16, [C.c_char_p])
            signatures["KPC_GetStatusBits"] = (C.c_uint32, [C.c_char_p])
            for name in ("SetOutputVoltage", "SetPositionControlMode"):
                signatures["KPC_" + name] = (C.c_short, [C.c_char_p, C.c_short])
            signatures["KPC_SetPosition"] = (C.c_short, [C.c_char_p, C.c_uint16])
            for name, (result, args) in signatures.items():
                function = getattr(dll, name)
                function.restype, function.argtypes = result, args
            self._dll = dll
        except (OSError, AttributeError) as exc:
            if self._dll_dir is not None:
                self._dll_dir.close()
                self._dll_dir = None
            raise KPCError(f"Cannot load Kinesis from {self.path}. Install Kinesis matching Python's bitness. {exc}") from exc

    @staticmethod
    def _check(code, operation):
        if code != 0:
            raise KPCError(f"{operation} failed (Kinesis error {code}).")

    def _call(self, name, *args):
        return getattr(self._dll, "KPC_" + name)(self.serial.encode("ascii"), *args)

    def discover(self):
        with self._lock:
            if self.simulate:
                return ["SIM-KPC101"]
            self._load()
            self._check(self._dll.TLI_BuildDeviceList(), "Build device list")
            buffer = C.create_string_buffer(65536)
            self._check(self._dll.TLI_GetDeviceListByTypeExt(buffer, len(buffer), 113), "Discover KPC101")
            return [s for s in buffer.value.decode("ascii").split(",") if s]

    def connect(self, serial):
        with self._lock:
            if self.serial is not None:
                raise KPCError("Disconnect the current device first.")
            serial = str(serial).strip()
            if serial not in self.discover():
                raise KPCError(f"KPC101 {serial!r} was not found. Check power, USB, and close other control apps.")
            self.serial = serial
            try:
                if not self.simulate:
                    self._check(self._call("Open"), "Open")
                    try:
                        if not self._call("LoadSettings"):
                            raise KPCError("Kinesis could not load the device settings. Configure the actuator in Kinesis first.")
                        if not self._call("StartPolling", 200):
                            raise KPCError("Could not start device polling.")
                        if not self._call("RequestMaxOutputVoltage") or not self._call("RequestPositionControlMode"):
                            raise KPCError("Could not request device configuration.")
                        self._check(self._call("RequestStatus"), "Request status")
                        time.sleep(0.3)
                    except Exception:
                        self._call("StopPolling")
                        self._call("Close")
                        raise
                try:
                    return self.status()
                except Exception:
                    self.disconnect()
                    raise
            except Exception:
                self.serial = None
                raise

    def disconnect(self):
        with self._lock:
            if self.serial is None:
                return
            try:
                if not self.simulate:
                    try:
                        self._call("StopPolling")
                    finally:
                        self._call("Close")
            finally:
                self.serial = None

    def _require(self):
        if self.serial is None:
            raise KPCError("Connect a KPC101 first.")
        if not self.simulate and not self._call("CheckConnection"):
            raise KPCError("USB connection to the KPC101 was lost.")

    def status(self):
        """Read cached values maintained by Kinesis polling (not a settled-motion guarantee)."""
        with self._lock:
            self._require()
            if self.simulate:
                zeroing = time.monotonic() < self._zero_until
                if self._zero_until and not zeroing:
                    self._zeroed = True
                bits = (0x100 | (0x80000000 if self._enabled else 0)
                        | (0x10 if self._zeroed else 0) | (0x20 if zeroing else 0))
                mode, maximum, voltage, position = self._mode, 75.0, self._voltage, self._position
            else:
                bits = self._call("GetStatusBits")
                try:
                    mode = Mode(self._call("GetPositionControlMode"))
                except ValueError as exc:
                    raise KPCError("Device control mode is not initialized.") from exc
                maximum = self._call("GetMaxOutputVoltage") / 10.0
                voltage = self._call("GetOutputVoltage") * maximum / 32767
                position = self._call("GetPosition") * 100.0 / 32767 if mode.closed_loop else None
            if maximum <= 0 or maximum > 150:
                raise KPCError(f"Invalid configured voltage limit: {maximum} V.")
            return Status(self.serial, mode, voltage, maximum,
                          position if mode.closed_loop else None, bool(bits & 0x80000000),
                          bool(bits & 0x100), bool(bits & 0x10), bool(bits & 0x20), bool(bits & 0x40000000), bits)

    def enable(self, enabled=True):
        with self._lock:
            self._require()
            if self.simulate:
                self._enabled = bool(enabled)
            else:
                self._check(self._call("Enable" if enabled else "Disable"), "Enable/disable")

    def _ready(self):
        status = self.status()
        if status.zeroing or status.error:
            raise KPCError("Device is zeroing or reports an error; wait or resolve the device error.")
        return status

    def set_mode(self, mode):
        with self._lock:
            mode = Mode(mode)
            status = self._ready()
            if mode.closed_loop and not status.feedback_connected:
                raise KPCError("Closed-loop control requires strain-gauge feedback.")
            if self.simulate:
                self._mode = mode
            else:
                self._check(self._call("SetPositionControlMode", mode.value), "Set mode")

    @staticmethod
    def _validate(value, maximum):
        value = float(value)
        if not math.isfinite(value) or not 0 <= value <= maximum:
            raise ValueError(f"Value must be finite and between 0 and {maximum}.")
        return value

    def set_voltage(self, volts):
        with self._lock:
            status = self._ready()
            volts = self._validate(volts, status.max_voltage)
            if status.mode.closed_loop or not status.enabled:
                raise KPCError("Voltage control requires enabled output in open-loop mode.")
            if self.simulate:
                self._voltage = volts
            else:
                self._check(self._call("SetOutputVoltage", round(volts / status.max_voltage * 32767)), "Set voltage")

    def set_position_percent(self, percent):
        with self._lock:
            status = self._ready()
            percent = self._validate(percent, 100)
            if not status.mode.closed_loop or not status.enabled or not status.feedback_connected:
                raise KPCError("Position control requires enabled output, closed-loop mode, and feedback.")
            if self.simulate:
                self._position = percent
            else:
                self._check(self._call("SetPosition", round(percent / 100 * 32767)), "Set position")

    def zero(self):
        """Start reference zeroing; monitor Status.zeroing/zeroed for completion."""
        with self._lock:
            status = self._ready()
            if not status.feedback_connected:
                raise KPCError("Zeroing requires strain-gauge feedback.")
            if self.simulate:
                self._zeroed = False
                self._zero_until = time.monotonic() + 10
            elif not self._call("SetZero"):
                raise KPCError("Device rejected reference zeroing.")

    def identify(self):
        with self._lock:
            self._require()
            if not self.simulate:
                self._call("Identify")

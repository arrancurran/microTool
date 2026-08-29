"""Mock camera backend for development without Ximea hardware or xiAPI."""

from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

from .hologram import calculate_hologram


class NoImage:
    """Small in-memory replacement for ``xiapi.Image``."""

    def __init__(self) -> None:
        self._data: np.ndarray | None = None
        self.tsSec = 0
        self.tsUSec = 0

    def set_image_data_numpy(self, data: np.ndarray) -> None:
        self._data = data

    def get_image_data_numpy(self) -> np.ndarray | None:
        return self._data


class NoCam:
    """In-memory replacement for ``xiapi.Camera`` used by the mock backend."""

    SENSOR_WIDTH = 2048
    SENSOR_HEIGHT = 2048

    def __init__(self) -> None:
        self.width = self.SENSOR_WIDTH
        self.height = self.SENSOR_HEIGHT
        self.exposure = 10_000.0
        self.framerate = 30.0
        self.offset_x = 0
        self.offset_y = 0
        self.debug_level = "XI_DL_WARNING"
        self._is_open = False
        self._is_running = False
        self._last_frame_time = 0.0
        self._spots: list[dict[str, float]] = [
            {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "intensity": 1.0,
                "vortex": 0.0,
                "phase": 0.0,
            }
        ]
        self._hologram: np.ndarray | None = None
        self._hologram_revision = 0
        self._rendered_revision = -1

    def open_device(self) -> bool:
        self._is_open = True
        return True

    def close_device(self) -> bool:
        self._is_running = False
        self._is_open = False
        return True

    def start_acquisition(self) -> bool:
        if not self._is_open:
            return False
        self._is_running = True
        self._last_frame_time = 0.0
        return True

    def stop_acquisition(self) -> bool:
        self._is_running = False
        return True

    def get_image(self, image: NoImage) -> bool:
        if not self._is_running:
            return False

        now = time.time()
        frame_time = 1.0 / max(self.framerate, 1.0)
        if now - self._last_frame_time < frame_time:
            return False

        revision = self._hologram_revision
        if self._hologram is None or self._rendered_revision != revision:
            hologram = calculate_hologram(
                self._spots,
                width=self.width,
                height=self.height,
            )
            # Do not mark a stale calculation as current if the UI supplied new
            # spots while this frame was being rendered.
            if revision == self._hologram_revision:
                self._hologram = hologram
                self._rendered_revision = revision
        else:
            hologram = self._hologram

        image.set_image_data_numpy(hologram)
        image.tsSec = int(now)
        image.tsUSec = int((now % 1) * 1_000_000)
        self._last_frame_time = now
        return True

    def get_device_name(self) -> bytes:
        return b"noCam"

    def set_spots(self, spots: list[dict[str, float]]) -> None:
        """Store a snapshot of the traps used for the next mock frame."""

        self._spots = [dict(spot) for spot in spots]
        self._hologram_revision += 1
        self._last_frame_time = 0.0

    def get_device_model_id(self) -> int:
        return 0

    def get_device_type(self) -> bytes:
        return b"Mock Camera"

    def get_device_sn(self) -> bytes:
        return b"NOCAM-0000"

    def get_exposure(self) -> float:
        return self.exposure

    def set_exposure(self, value: float) -> bool:
        self.exposure = float(value)
        return True

    def get_exposure_minimum(self) -> float:
        return 1.0

    def get_exposure_maximum(self) -> float:
        return 1_000_000.0

    def get_framerate(self) -> float:
        return self.framerate

    def set_framerate(self, value: float) -> bool:
        self.framerate = float(value)
        return True

    def get_framerate_minimum(self) -> float:
        return 1.0

    def get_framerate_maximum(self) -> float:
        return 100.0

    def get_framerate_increment(self) -> float:
        return 1.0

    def get_width(self) -> int:
        return self.width

    def set_width(self, value: int) -> bool:
        self.width = int(value)
        self._hologram_revision += 1
        self._last_frame_time = 0.0
        return True

    def get_width_minimum(self) -> int:
        return 1

    def get_width_maximum(self) -> int:
        return self.SENSOR_WIDTH

    def get_width_increment(self) -> int:
        return 1

    def get_height(self) -> int:
        return self.height

    def set_height(self, value: int) -> bool:
        self.height = int(value)
        self._hologram_revision += 1
        self._last_frame_time = 0.0
        return True

    def get_height_minimum(self) -> int:
        return 1

    def get_height_maximum(self) -> int:
        return self.SENSOR_HEIGHT

    def get_height_increment(self) -> int:
        return 1

    def get_offsetX(self) -> int:
        return self.offset_x

    def set_offsetX(self, value: int) -> bool:
        self.offset_x = int(value)
        return True

    def get_offsetX_minimum(self) -> int:
        return 0

    def get_offsetX_maximum(self) -> int:
        return self.SENSOR_WIDTH

    def get_offsetX_increment(self) -> int:
        return 1

    def get_offsetY(self) -> int:
        return self.offset_y

    def set_offsetY(self, value: int) -> bool:
        self.offset_y = int(value)
        return True

    def get_offsetY_minimum(self) -> int:
        return 0

    def get_offsetY_maximum(self) -> int:
        return self.SENSOR_HEIGHT

    def get_offsetY_increment(self) -> int:
        return 1

    def get_debug_level(self) -> str:
        return self.debug_level

    def set_debug_level(self, value: str) -> bool:
        self.debug_level = str(value)
        return True


class CameraControl:
    """Mock implementation of the public Ximea ``CameraControl`` interface."""

    def __init__(self) -> None:
        self.camera: NoCam | None = None
        self.image: NoImage | None = None
        self.set_commands_by_name: dict[str, dict[str, Any]] = {}
        self.get_commands_by_name: dict[str, dict[str, Any]] = {}
        self.camera_lock = Lock()

    def _load_commands_from_json(self) -> None:
        commands_path = Path(__file__).resolve().parent / "commands.json"
        with commands_path.open("r", encoding="utf-8") as file:
            commands = json.load(file)
        self.set_commands_by_name = {cmd["name"]: cmd for cmd in commands["set"]}
        self.get_commands_by_name = {cmd["name"]: cmd for cmd in commands["get"]}

    def start_command_thread(self) -> None:
        """Compatibility no-op; mock commands execute synchronously."""

    def stop_command_thread(self) -> None:
        """Compatibility no-op; mock commands execute synchronously."""

    def call_camera_command(
        self, friendly_name: str, method: str, value: Any = None
    ) -> Any:
        if self.camera is None:
            return None

        commands = (
            self.set_commands_by_name if method == "set" else self.get_commands_by_name
        )
        command = commands.get(friendly_name)
        if command is None:
            return None

        camera_method = getattr(self.camera, f"{method}_{command['cmd']}", None)
        if camera_method is None:
            return None

        with self.camera_lock:
            if method == "get":
                return camera_method()

            value_type = command.get("type", "float")
            if value_type == "float":
                value = float(value)
            elif value_type == "int":
                value = int(value)
            elif value_type == "str":
                value = str(value)
            camera_method(value)
            # Match the Ximea controller, whose queued set operations do not
            # return a result to callers.
            return None

    def initialize_camera(self) -> None:
        if self.camera is None:
            self.camera = NoCam()
            self._load_commands_from_json()
            self.start_command_thread()

    def open_camera(self) -> None:
        if self.camera is not None:
            self.camera.open_device()

    def ImageObject(self) -> None:
        if self.image is None:
            self.image = NoImage()

    def start_camera(self) -> None:
        if self.camera is not None:
            self.camera.start_acquisition()

    def get_image(self) -> bool | None:
        if self.camera is not None and self.image is not None:
            return self.camera.get_image(self.image)
        return None

    def get_image_data(self) -> np.ndarray | None:
        if self.image is not None:
            return self.image.get_image_data_numpy()
        return None

    def get_image_timestamp(self) -> float | None:
        if self.image is not None:
            return self.image.tsSec + self.image.tsUSec / 1_000_000
        return None

    def set_spots(self, spots: list[dict[str, float]]) -> None:
        """Update the traps rendered by subsequent mock camera frames."""

        if self.camera is not None:
            self.camera.set_spots(spots)

    def stop_camera(self) -> None:
        if self.camera is not None:
            self.camera.stop_acquisition()

    def close(self) -> None:
        self.stop_command_thread()
        if self.camera is not None:
            self.camera.close_device()
            self.camera = None


class CameraSequences:
    """Mock implementation of the public Ximea ``CameraSequences`` interface."""

    def __init__(self, camera_control: CameraControl) -> None:
        self.camera_control = camera_control

    def connect_camera(self) -> None:
        self.camera_control.initialize_camera()
        self.camera_control.open_camera()
        self.camera_control.ImageObject()

    def disconnect_camera(self) -> None:
        self.camera_control.close()

    def acquire_time_series(self, num_images: int) -> bool | None:
        for _ in range(num_images):
            return self.camera_control.get_image()
        return None

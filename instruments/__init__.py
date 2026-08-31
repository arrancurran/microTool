"""Camera backend selection.

The imports are intentionally lazy so the mock backend does not require xiAPI to
be installed. Existing ``from instruments import CameraControl`` imports still
resolve to the default Ximea backend.
"""

from importlib import import_module
from typing import Any


def get_camera_backend(name: str = "xicam") -> tuple[type[Any], type[Any]]:
    """Return CameraControl and CameraSequences for the requested backend."""
    normalized_name = name.lower()
    if normalized_name not in {"xicam", "nocam"}:
        raise ValueError(f"Unknown camera backend: {name}")

    module_name = ".xicam" if normalized_name == "xicam" else ".noCam"
    module = import_module(module_name, __name__)
    return module.CameraControl, module.CameraSequences


def __getattr__(name: str) -> Any:
    if name in {"CameraControl", "CameraSequences"}:
        camera_control, camera_sequences = get_camera_backend("xicam")
        return camera_control if name == "CameraControl" else camera_sequences
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["CameraControl", "CameraSequences", "get_camera_backend"]

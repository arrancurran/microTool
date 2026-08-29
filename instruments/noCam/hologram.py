"""Grating-and-lens hologram generation for the mock camera backend."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import numpy as np


DEFAULT_WAVELENGTH_M = 1064e-9
DEFAULT_PIXEL_PITCH_M = 8e-6
DEFAULT_FOCAL_LENGTH_M = 0.003


def calculate_hologram(
    spots: Iterable[Mapping[str, float]],
    width: int,
    height: int,
    *,
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
    pixel_pitch_m: float = DEFAULT_PIXEL_PITCH_M,
    focal_length_m: float = DEFAULT_FOCAL_LENGTH_M,
) -> np.ndarray:
    """Return an 8-bit phase hologram for the supplied optical traps.

    Spot ``x``, ``y``, and ``z`` coordinates are interpreted as micrometres.
    Lateral displacement is encoded with a blazed grating, axial displacement
    with a quadratic lens, and multiple spots are combined by complex-field
    superposition. ``phase`` is expressed in degrees and ``vortex`` is the
    integer or fractional azimuthal charge used by the existing spot UI.
    """

    if width <= 0 or height <= 0:
        raise ValueError("Hologram width and height must be positive")
    if wavelength_m <= 0 or pixel_pitch_m <= 0 or focal_length_m <= 0:
        raise ValueError("Optical parameters must be positive")

    spots = list(spots)
    if not spots:
        return np.zeros((height, width), dtype=np.uint8)

    x_slm = (
        np.arange(width, dtype=np.float32) - np.float32((width - 1) / 2.0)
    ) * np.float32(pixel_pitch_m)
    y_slm = (
        np.arange(height, dtype=np.float32) - np.float32((height - 1) / 2.0)
    ) * np.float32(pixel_pitch_m)

    x_grid = x_slm[None, :]
    y_grid = y_slm[:, None]
    radius_squared = x_grid * x_grid + y_grid * y_grid
    azimuth = np.arctan2(y_grid, x_grid)

    wave_number_over_focal_length = np.float32(
        (2.0 * np.pi) / (wavelength_m * focal_length_m)
    )
    lens_coefficient = np.float32(
        -np.pi / (wavelength_m * focal_length_m * focal_length_m)
    )
    field = np.zeros((height, width), dtype=np.complex64)

    for spot in spots:
        intensity = max(0.0, float(spot.get("intensity", 1.0)))
        if intensity == 0.0:
            continue

        x_focus = np.float32(float(spot.get("x", 0.0)) * 1e-6)
        y_focus = np.float32(float(spot.get("y", 0.0)) * 1e-6)
        z_focus = np.float32(float(spot.get("z", 0.0)) * 1e-6)
        phase_offset = np.float32(
            np.deg2rad(float(spot.get("phase", 0.0)))
        )
        vortex_charge = np.float32(float(spot.get("vortex", 0.0)))

        phase = (
            wave_number_over_focal_length
            * (x_focus * x_grid + y_focus * y_grid)
            + lens_coefficient * z_focus * radius_squared
            + vortex_charge * azimuth
            + phase_offset
        )
        field += np.float32(np.sqrt(intensity)) * np.exp(
            1j * phase
        ).astype(np.complex64)

    wrapped_phase = np.mod(np.angle(field), 2.0 * np.pi)
    return np.rint(wrapped_phase * (255.0 / (2.0 * np.pi))).astype(np.uint8)

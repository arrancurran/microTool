import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Store last-session state in the project root (same folder as app.py)
_BASE_DIR = Path(__file__).resolve().parent.parent
_SESSION_PATH = _BASE_DIR / "last_session.json"


def _safe_getattr(obj: Any, name: str) -> Any:
    """Return getattr(obj, name) or None if missing.
    """
    try:
        return getattr(obj, name)
    except AttributeError:
        return None


def save_last_session(window: Any, camera_control: Any) -> None:
    """Persist front-panel settings to last_session.json.

    Captures ROI spinboxes, exposure, SLM centre alignment, and experiment
    settings so they can be restored on the next run.
    """

    data: Dict[str, Any] = {}

    # --- ROI settings ---
    roi: Dict[str, Any] = {}
    for key in ("width", "height", "offset_x", "offset_y"):
        spin = _safe_getattr(window, f"roi_{key}")
        if spin is not None:
            try:
                roi[key] = int(spin.value())
            except Exception as e:
                logger.error(f"Error reading ROI spinbox {key}: {e}")
        else:
            # Fallback to camera value if UI element is missing
            try:
                val = camera_control.call_camera_command(key, "get")
                if val is not None:
                    roi[key] = int(val)
            except Exception as e:
                logger.error(f"Error reading ROI {key} from camera: {e}")
    if roi:
        data["roi"] = roi

    # --- Exposure setting ---
    exposure_value = None
    try:
        exposure_value = camera_control.call_camera_command("exposure", "get")
    except Exception as e:
        logger.error(f"Error reading exposure from camera: {e}")

    if exposure_value is None:
        slider = _safe_getattr(window, "exposure_slider")
        if slider is not None:
            try:
                exposure_value = int(slider.value())
            except Exception as e:
                logger.error(f"Error reading exposure slider: {e}")

    if exposure_value is not None:
        try:
            data["exposure_us"] = float(exposure_value)
        except Exception:
            pass

    # --- SLM centre / camera overlay alignment ---
    slm_centre: Dict[str, float] = {}
    for axis in ("x", "y"):
        spin = _safe_getattr(window, f"camera_centre_{axis}_spin")
        if spin is not None:
            try:
                slm_centre[axis] = float(spin.value())
            except Exception as e:
                logger.error(f"Error reading SLM centre {axis}: {e}")
    if slm_centre:
        data["slm_centre"] = slm_centre

    # --- SLM coordinate scaling ---
    slm_scales: Dict[str, float] = {}
    for axis in ("x", "y", "z"):
        spin = _safe_getattr(window, f"slm_{axis}_scale_spin")
        if spin is not None:
            try:
                slm_scales[axis] = float(spin.value())
            except Exception as e:
                logger.error(f"Error reading SLM {axis.upper()} scale: {e}")
    if slm_scales:
        data["slm_scales"] = slm_scales

    # --- Experiment / acquisition settings ---
    experiment: Dict[str, Any] = {}

    combo = _safe_getattr(window, "acquisition_mode_combo")
    if combo is not None:
        try:
            experiment["mode"] = combo.currentText()
        except Exception as e:
            logger.error(f"Error reading acquisition mode: {e}")

    for attr, key in (
        ("experiment_dir_edit", "directory"),
        ("experiment_name_edit", "name"),
        ("experiment_framerate_edit", "framerate_hz"),
        ("experiment_frames_edit", "frames"),
    ):
        widget = _safe_getattr(window, attr)
        if widget is not None and hasattr(widget, "text"):
            try:
                experiment[key] = widget.text()
            except Exception as e:
                logger.error(f"Error reading experiment field {key}: {e}")

    if experiment:
        data["experiment"] = experiment

    if not data:
        # Nothing to persist
        return

    try:
        _SESSION_PATH.write_text(json.dumps(data, indent=2))
        logger.info(f"Last session settings saved to {_SESSION_PATH}")
    except Exception as e:
        logger.error(f"Error writing last session file {_SESSION_PATH}: {e}")


def load_last_session(window: Any, camera_control: Any) -> None:
    """Load last-session settings from last_session.json and apply them.

    This updates the front-panel widgets and, where appropriate, uses the
    existing control plumbing (spinbox/slider signals) to push changes to
    the camera.
    """

    if not _SESSION_PATH.exists():
        return

    try:
        raw = _SESSION_PATH.read_text()
        data = json.loads(raw)
    except Exception as e:
        logger.error(f"Error reading last session file {_SESSION_PATH}: {e}")
        return

    # --- ROI restore ---
    roi = data.get("roi", {}) or {}
    for key in ("width", "height", "offset_x", "offset_y"):
        if key not in roi:
            continue
        val = roi.get(key)
        if val is None:
            continue

        spin = _safe_getattr(window, f"roi_{key}")
        applied = False
        if spin is not None:
            try:
                spin.setValue(int(val))
                applied = True  # ROIControl's valueChanged will update camera
            except Exception as e:
                logger.error(f"Error restoring ROI spinbox {key}: {e}")

        if not applied:
            # Fallback: write directly to camera
            try:
                camera_control.call_camera_command(key, "set", int(val))
            except Exception as e:
                logger.error(f"Error restoring ROI {key} to camera: {e}")

    # --- Exposure restore ---
    exposure_val = data.get("exposure_us")
    if exposure_val is not None:
        slider = _safe_getattr(window, "exposure_slider")
        if slider is not None:
            try:
                slider.setValue(int(round(float(exposure_val))))
            except Exception as e:
                logger.error(f"Error restoring exposure slider: {e}")
        else:
            try:
                camera_control.call_camera_command("exposure", "set", float(exposure_val))
            except Exception as e:
                logger.error(f"Error restoring exposure on camera: {e}")

    # --- SLM centre / camera overlay alignment restore ---
    slm_centre = data.get("slm_centre", {}) or {}
    for axis in ("x", "y"):
        if axis not in slm_centre:
            continue
        spin = _safe_getattr(window, f"camera_centre_{axis}_spin")
        if spin is not None:
            try:
                spin.setValue(float(slm_centre[axis]))
            except (TypeError, ValueError) as e:
                logger.error(f"Error restoring SLM centre {axis}: {e}")

    # --- SLM coordinate scaling restore ---
    slm_scales = data.get("slm_scales", {}) or {}
    restored_slm_scale = False
    for axis in ("x", "y", "z"):
        if axis not in slm_scales:
            continue
        spin = _safe_getattr(window, f"slm_{axis}_scale_spin")
        if spin is not None:
            signals_were_blocked = None
            try:
                if hasattr(spin, "blockSignals"):
                    signals_were_blocked = spin.blockSignals(True)
                spin.setValue(float(slm_scales[axis]))
                restored_slm_scale = True
            except (TypeError, ValueError) as e:
                logger.error(f"Error restoring SLM {axis.upper()} scale: {e}")
            finally:
                if signals_were_blocked is not None:
                    spin.blockSignals(signals_were_blocked)

    # Apply all three restored values atomically and send one updated payload.
    apply_slm_calibration = _safe_getattr(window, "_on_slm_scale_changed")
    if restored_slm_scale and callable(apply_slm_calibration):
        try:
            apply_slm_calibration()
        except Exception as e:
            logger.error(f"Error applying restored SLM scales: {e}")

    # --- Experiment / acquisition settings restore ---
    experiment = data.get("experiment", {}) or {}

    mode_text = experiment.get("mode")
    combo = _safe_getattr(window, "acquisition_mode_combo")
    if combo is not None and isinstance(mode_text, str):
        try:
            index = combo.findText(mode_text)
            if index >= 0:
                combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Error restoring acquisition mode: {e}")

    for attr, key in (
        ("experiment_dir_edit", "directory"),
        ("experiment_name_edit", "name"),
        ("experiment_framerate_edit", "framerate_hz"),
        ("experiment_frames_edit", "frames"),
    ):
        if key not in experiment:
            continue
        val = experiment.get(key)
        widget = _safe_getattr(window, attr)
        if widget is not None and hasattr(widget, "setText") and isinstance(val, str):
            try:
                widget.setText(val)
            except Exception as e:
                logger.error(f"Error restoring experiment field {key}: {e}")

    # Refresh derived acquisition estimates if possible
    ui_methods = getattr(getattr(window, "image_container", None), "ui_methods", None)
    if ui_methods is not None and hasattr(ui_methods, "update_acquisition_estimates"):
        try:
            ui_methods.update_acquisition_estimates()
        except Exception as e:
            logger.error(f"Error updating acquisition estimates after last-session restore: {e}")

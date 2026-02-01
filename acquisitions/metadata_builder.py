import logging
from datetime import datetime

from utils import get_computer_name

logger = logging.getLogger(__name__)


def build_metadata(
    acquisition_type: str,
    window,
    camera_control,
    roi_width: int | None,
    roi_height: int | None,
    *,
    start_time: datetime | None = None,
    requested_frames: int | None = None,
    acquired_frames: int | None = None,
    mode: str | None = None,
    requested_framerate: float | None = None,
    effective_framerate: float | None = None,
):
    """Build metadata dictionary for HDF5 files.

    Parameters are intentionally high-level; this function is
    responsible for querying the camera and window where needed.
    """

    metadata: dict[str, object] = {}

    try:
        metadata["Computer Name"] = get_computer_name()
    except Exception as e:
        logger.error(f"Error getting computer name for metadata: {e}")

    metadata["Acquisition Type"] = acquisition_type

    if mode is not None:
        metadata["Acquisition Mode"] = mode

    try:
        app_info = window.ui_scaffolding.get("app", {})
        metadata["Software Name"] = app_info.get("name")
        metadata["Software Version"] = app_info.get("version")
    except Exception as e:
        logger.error(f"Error getting app info for metadata: {e}")

    try:
        cam_name = camera_control.camera.get_device_name()
        metadata["Camera Model"] = cam_name.decode("utf-8") if isinstance(cam_name, bytes) else cam_name
    except Exception as e:
        logger.error(f"Error getting camera model for metadata: {e}")

    # Timing information
    try:
        if start_time is None:
            start_time = datetime.now()
        metadata["Start Time"] = start_time.isoformat()
        metadata["End Time"] = datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Error setting timing metadata: {e}")

    # Exposure
    try:
        metadata["Exposure"] = camera_control.call_camera_command("exposure", "get")
    except Exception as e:
        logger.error(f"Error getting exposure for metadata: {e}")

    # Framerate information
    try:
        if effective_framerate is None:
            # Fall back to current camera report if not provided
            effective_framerate = camera_control.call_camera_command("framerate", "get")
        if effective_framerate is not None:
            metadata["Framerate"] = float(effective_framerate)
    except Exception as e:
        logger.error(f"Error getting framerate for metadata: {e}")

    # Requested framerate depends on acquisition type and mode
    requested_for_metadata: float | None = None
    if acquisition_type.lower() == "experiment":
        try:
            if mode == "Free run (max speed)":
                requested_for_metadata = camera_control.call_camera_command("framerate_max", "get")
            elif mode == "Frame rate mode" and requested_framerate is not None:
                requested_for_metadata = requested_framerate
        except Exception as e:
            logger.error(f"Error determining requested framerate for metadata: {e}")

    if requested_for_metadata is not None:
        metadata["Requested Framerate"] = float(requested_for_metadata)

    # Frame counts
    if requested_frames is not None:
        metadata["Requested Frames"] = int(requested_frames)
    if acquired_frames is not None:
        metadata["Acquired Frames"] = int(acquired_frames)

    # ROI and offsets
    try:
        if roi_width is not None:
            metadata["ROI Width"] = int(roi_width)
        if roi_height is not None:
            metadata["ROI Height"] = int(roi_height)

        metadata["ROI Offset X"] = camera_control.call_camera_command("offset_x", "get")
        metadata["ROI Offset Y"] = camera_control.call_camera_command("offset_y", "get")
    except Exception as e:
        logger.error(f"Error getting ROI/offsets for metadata: {e}")

    return metadata

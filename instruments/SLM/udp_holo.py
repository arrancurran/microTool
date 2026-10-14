from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple, Optional
import logging
import math
import socket
import atexit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpotRow:
    """Represents one line inside <spots> ... </spots>."""
    cols: Tuple[float, ...]


@dataclass(frozen=True)
class UdpHoloMessage:
    spots: Sequence[SpotRow]
    totalA: float
    blazing: Sequence[float]  # LUT / ramp table (0..1)
    zernike: Sequence[float]  # coefficient list
    window_rect: Tuple[int, int, int, int]  # x0, y0, w, h
    aspect: Tuple[float, float]  # ax, ay
    centre: Tuple[float, float]  # cx, cy (likely 0..1)


def _fmt_fixed(x: float) -> str:
    """Match LabVIEW's six-decimal fixed-point formatting."""
    if abs(x) < 0.5e-6:
        x = 0.0
    return f"{x:.6f}"


def _fmt_scientific(x: float) -> str:
    """Match LabVIEW's ``0.000000E+0`` scientific notation."""
    if x == 0.0:
        x = 0.0  # Do not serialize negative zero.
    mantissa, exponent = f"{x:.6E}".split("E")
    return f"{mantissa}E{int(exponent):+d}"


def _fmt_spot(cols: Sequence[float]) -> str:
    """Format the nine fields of one LabVIEW spot record."""
    if len(cols) != 9:
        raise ValueError(f"A spot must contain 9 columns, got {len(cols)}")

    x, y, z, intensity, vortex, phase, offset_x, offset_y, amplitude = cols
    fields = (
        _fmt_scientific(x),
        _fmt_scientific(y),
        _fmt_scientific(z),
        _fmt_fixed(intensity),
        str(int(vortex)),
        _fmt_fixed(phase),
        _fmt_fixed(offset_x),
        _fmt_fixed(offset_y),
        _fmt_fixed(amplitude),
    )
    # LabVIEW includes one leading space before each spot record.
    return " " + " ".join(fields)


def build_payload_text(msg: UdpHoloMessage) -> str:
    """Build the textual payload for the SLM UDP protocol."""
    lines: list[str] = []
    lines.append("<data>")

    lines.append("<spots>")
    for s in msg.spots:
        lines.append(_fmt_spot(s.cols))
    lines.append("</spots>")

    lines.append("<totalA>")
    lines.append(_fmt_fixed(msg.totalA))
    lines.append("</totalA>")

    lines.append("<blazing>")
    for v in msg.blazing:
        lines.append(_fmt_fixed(v))
    lines.append("</blazing>")

    lines.append("<zernike>")
    for c in msg.zernike:
        lines.append(_fmt_fixed(c))
    lines.append("</zernike>")

    x0, y0, w, h = msg.window_rect
    lines.append("<window_rect>")
    lines.append(f"{x0}, {y0}, {w}, {h}, ")
    lines.append("</window_rect>")

    ax, ay = msg.aspect
    lines.append("<aspect>")
    lines.append(f"{_fmt_fixed(ax)}, {_fmt_fixed(ay)}")
    lines.append("</aspect>")

    cx, cy = msg.centre
    lines.append("<centre>")
    lines.append(f"{_fmt_fixed(cx)}, {_fmt_fixed(cy)}")
    lines.append("</centre>")

    lines.append("</data>")
    return "\n".join(lines) + "\n"


# -----------------------------
# LabVIEW-like UDP "Open + Write"
# -----------------------------

class LabviewUdpClient:
    """
    Mimics LabVIEW:
      - UDP Open: bind local/source port once (connection ID)
      - UDP Write: send many times to remote ip:port using same socket
    """

    def __init__(
        self,
        local_host: str,
        local_port: int,
        remote_host: str,
        remote_port: int,
    ) -> None:
        self.remote = (remote_host, remote_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # On Windows, REUSEADDR can silently share an occupied UDP port.
            # Fail clearly instead of competing with another application.
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            self.sock.settimeout(0.2)
            self.sock.bind((local_host, local_port))
            self.sock.connect(self.remote)
        except OSError:
            self.sock.close()
            logger.exception(
                "Cannot open SLM UDP %s:%s -> %s:%s. Check for another microTool "
                "or diagnostic listener using the source port.",
                local_host, local_port, remote_host, remote_port,
            )
            raise
        logger.info("Opened SLM UDP %s -> %s", self.sock.getsockname(), self.remote)

    def write_text(self, payload: str) -> None:
        data = payload.encode("utf-8")
        # UDP Write(address=remote_host, port=remote_port, data=payload)
        sent = self.sock.send(data)
        logger.debug("Submitted %s UDP bytes to %s (delivery is not acknowledged)", sent, self.remote)

    def close(self) -> None:
        self.sock.close()


# -----------------------------
# Connection params
# -----------------------------

# LabVIEW: UDP Open uses port=61556 => local/source port
SLM_LOCAL_HOST: str = "127.0.0.1"
SLM_LOCAL_PORT: int = 61556

# LabVIEW: UDP Write sends to 127.0.0.1:61557 => remote/destination
SLM_HOST: str = "127.0.0.1"
SLM_PORT: int = 61557

_udp_client: Optional[LabviewUdpClient] = None


def get_udp_client() -> LabviewUdpClient:
    """Create (once) and return the reusable UDP client."""
    global _udp_client
    if _udp_client is None:
        _udp_client = LabviewUdpClient(
            local_host=SLM_LOCAL_HOST,
            local_port=SLM_LOCAL_PORT,
            remote_host=SLM_HOST,
            remote_port=SLM_PORT,
        )
    return _udp_client


def close_udp_client() -> None:
    """Release the source port; the next send opens a fresh socket."""
    global _udp_client
    client, _udp_client = _udp_client, None
    if client is not None:
        client.close()


atexit.register(close_udp_client)


# Reusable defaults for fields that are not yet controlled via the UI.
DEFAULT_BLAZING: Sequence[float] = [
    0.000000,
    0.019028,
    0.038486,
    0.058803,
    0.080407,
    0.103730,
    0.129198,
    0.157243,
    0.188294,
    0.222752,
    0.260533,
    0.301132,
    0.344029,
    0.388706,
    0.434645,
    0.481327,
    0.528233,
    0.574844,
    0.620643,
    0.665109,
    0.707724,
    0.747971,
    0.785329,
    0.819368,
    0.850262,
    0.878442,
    0.904337,
    0.928379,
    0.950999,
    0.972628,
    0.993695,
    1.000000,
]



# Engine order: astigmatism, defocus, astigmatism, trefoil, coma, coma,
# trefoil, trefoil, astigmatism, spherical, astigmatism, trefoil.
# Coefficients are passed through in engine units without local evaluation.
DEFAULT_ZERNIKE: Sequence[float] = [8.0] + [0.0] * 11
ZERNIKE_CORRECTION_INDICES = {
    "astigmatism_1": 0,
    "astigmatism_2": 2,
    "coma_1": 4,
    "coma_2": 5,
}


def get_zernike_coefficients() -> list[float]:
    """Build the engine's 12 slots, keeping unsupported modes at zero."""
    coefficients = [0.0] * 12
    for index in ZERNIKE_CORRECTION_INDICES.values():
        coefficients[index] = DEFAULT_ZERNIKE[index]
    return coefficients


def get_aberration_coefficients() -> dict[str, float]:
    """Return the active UDP coefficients controlled by calibration."""
    return {name: DEFAULT_ZERNIKE[index]
            for name, index in ZERNIKE_CORRECTION_INDICES.items()}


def set_aberration_coefficients(**coefficients: float) -> None:
    """Replace selected UDP coefficients, preserving all other calibration."""
    unknown = coefficients.keys() - ZERNIKE_CORRECTION_INDICES.keys()
    if unknown:
        raise ValueError(f"Unknown aberration coefficients: {sorted(unknown)}")
    values = {name: float(value) for name, value in coefficients.items()}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Aberration coefficients must be finite numbers")
    global DEFAULT_ZERNIKE
    updated = get_zernike_coefficients()
    for name, value in values.items():
        updated[ZERNIKE_CORRECTION_INDICES[name]] = value
    DEFAULT_ZERNIKE = updated


DEFAULT_WINDOW_RECT: Tuple[int, int, int, int] = (2560, 0, 512, 512)

# Scaling factors for spot coordinates before sending to the SLM
X_SCALE: float = -1.84e-5
Y_SCALE: float = 1.86e-5
Z_SCALE: float = -1.631e-5


def get_coordinate_scales() -> Tuple[float, float, float]:
    """Return the active X, Y, and Z SLM coordinate scale factors."""

    return X_SCALE, Y_SCALE, Z_SCALE


def set_coordinate_scales(x_scale: float, y_scale: float, z_scale: float) -> None:
    """Set the scale factors used when converting traps for the SLM."""

    scales = (float(x_scale), float(y_scale), float(z_scale))
    if not all(math.isfinite(value) for value in scales):
        raise ValueError("SLM coordinate scales must be finite numbers")

    global X_SCALE, Y_SCALE, Z_SCALE
    X_SCALE, Y_SCALE, Z_SCALE = scales


def build_message_from_traps(traps: Iterable[Mapping[str, float]]) -> UdpHoloMessage:
    """Convert a collection of optical trap dicts into a UdpHoloMessage."""
    spots: list[SpotRow] = []
    totalA = 0.0

    for t in traps:
        intensity = float(t.get("intensity", 0.0))

        x = float(t.get("x", 0.0))
        y = float(t.get("y", 0.0))
        z = float(t.get("z", 0.0))

        x_s = x * X_SCALE
        y_s = y * Y_SCALE
        z_s = z * Z_SCALE

        vortex = float(t.get("vortex", 0.0))
        phase = float(t.get("phase", 0.0))

        cols = (x_s, y_s, z_s, intensity, int(vortex), phase, 0.0, 0.0, 1.0)
        spots.append(SpotRow(cols=cols))
        totalA += intensity

    return UdpHoloMessage(
        spots=spots,
        totalA=totalA,
        blazing=DEFAULT_BLAZING,
        zernike=get_zernike_coefficients(),
        window_rect=DEFAULT_WINDOW_RECT,
        aspect=(1.0, 1.0),
        centre=(0.5, 0.5),
    )


def send_traps(traps: Iterable[Mapping[str, float]]) -> None:
    """Build and send an SLM hologram message for the given traps."""
    traps = list(traps)
    logger.debug(f"send_traps called with {len(traps)} trap(s): {traps}")
    msg = build_message_from_traps(traps)
    payload = build_payload_text(msg)

    if len(payload.encode("utf-8")) > 65507:
        raise ValueError("SLM payload exceeds the IPv4 UDP datagram limit (65507 bytes)")
    for attempt in range(2):
        client = get_udp_client()
        try:
            client.write_text(payload)
            return
        except OSError:
            close_udp_client()
            if attempt:
                raise
            logger.warning("SLM UDP send failed; reopening the socket and retrying once", exc_info=True)


if __name__ == "__main__":
    example_traps = [
        {"x": 0.0, "y": 0.0, "z": 0.0, "intensity": 1.0, "vortex": 10.0, "phase": 0.0},
    ]

    print(build_payload_text(build_message_from_traps(example_traps)))

    # Send a packet (will come from local port 61556, and go to 127.0.0.1:61557)
    send_traps(example_traps)

    # Optional cleanup
    close_udp_client()

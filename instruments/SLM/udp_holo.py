from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple, Optional
import socket


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


def _fmt_float(x: float) -> str:
    """Format floats in a LabVIEW-ish readable style."""
    ax = abs(x)
    if (ax != 0.0) and (ax < 1e-3 or ax >= 1e4):
        return f"{x:.6E}"
    return f"{x:.6f}"


def build_payload_text(msg: UdpHoloMessage) -> str:
    """Build the textual payload for the SLM UDP protocol."""
    lines: list[str] = []
    lines.append("<data>")

    lines.append("<spots>")
    for s in msg.spots:
        lines.append(" ".join(_fmt_float(v) for v in s.cols))
    lines.append("</spots>")

    lines.append("<totalA>")
    lines.append(_fmt_float(msg.totalA))
    lines.append("</totalA>")

    lines.append("<blazing>")
    for v in msg.blazing:
        lines.append(_fmt_float(v))
    lines.append("</blazing>")

    lines.append("<zernike>")
    for c in msg.zernike:
        lines.append(_fmt_float(c))
    lines.append("</zernike>")

    x0, y0, w, h = msg.window_rect
    lines.append("<window_rect>")
    lines.append(f"{x0}, {y0}, {w}, {h},")
    lines.append("</window_rect>")

    ax, ay = msg.aspect
    lines.append("<aspect>")
    lines.append(f"{_fmt_float(ax)}, {_fmt_float(ay)}")
    lines.append("</aspect>")

    cx, cy = msg.centre
    lines.append("<centre>")
    lines.append(f"{_fmt_float(cx)}, {_fmt_float(cy)}")
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
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # UDP Open(port=local_port)
        self.sock.bind((local_host, local_port))

    def write_text(self, payload: str) -> None:
        data = payload.encode("utf-8")
        # UDP Write(address=remote_host, port=remote_port, data=payload)
        self.sock.sendto(data, self.remote)

    def close(self) -> None:
        self.sock.close()


# -----------------------------
# Connection params (FIXED: ports swapped to match your LabVIEW description)
# -----------------------------

# LabVIEW: UDP Open uses 61557  => local/source port
SLM_LOCAL_HOST: str = "127.0.0.1"
SLM_LOCAL_PORT: int = 61557

# LabVIEW: UDP Write sends to 127.0.0.1:61556 => remote/destination
SLM_HOST: str = "127.0.0.1"
SLM_PORT: int = 61556

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
    """Optional: call on program exit."""
    global _udp_client
    if _udp_client is not None:
        _udp_client.close()
        _udp_client = None


# Reusable defaults for fields that are not yet controlled via the UI.
DEFAULT_BLAZING: Sequence[float] = [
    0.0, 0.061207, 0.121163, 0.178615, 0.232312, 0.281003, 0.323435, 0.358392,
    0.385699, 0.406379, 0.421520, 0.432209, 0.439535, 0.444586, 0.448449, 0.452214,
    0.456968, 0.463798, 0.473794, 0.488043, 0.507634, 0.533624, 0.566254, 0.604853,
    0.648701, 0.697080, 0.749270, 0.804552, 0.862208, 0.921519, 0.981766, 1.0,
]

DEFAULT_ZERNIKE: Sequence[float] = [7.0, 0.0, -7.0] + [0.0] * 9
DEFAULT_WINDOW_RECT: Tuple[int, int, int, int] = (2560, 0, 512, 512)

# Scaling factors for spot coordinates before sending to the SLM
X_SCALE: float = -1.84e-5
Y_SCALE: float = 1.86e-5
Z_SCALE: float = -1.631e-5


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

        cols = (x_s, y_s, z_s, intensity, vortex, phase, 0.0, 0.0, 1.0)
        spots.append(SpotRow(cols=cols))
        totalA += intensity

    return UdpHoloMessage(
        spots=spots,
        totalA=totalA,
        blazing=DEFAULT_BLAZING,
        zernike=DEFAULT_ZERNIKE,
        window_rect=DEFAULT_WINDOW_RECT,
        aspect=(1.0, 1.0),
        centre=(0.5, 0.5),
    )


def send_traps(traps: Iterable[Mapping[str, float]]) -> None:
    """Build and send an SLM hologram message for the given traps."""
    msg = build_message_from_traps(traps)
    payload = build_payload_text(msg)

    client = get_udp_client()
    client.write_text(payload)


if __name__ == "__main__":
    example_traps = [
        {"intensity": 1.0, "x": -1.84e-4, "y": -1.86e-4, "z": 0.0, "vortex": 0.0, "phase": 0.0},
        {"intensity": 0.0, "x": -1.104e-4, "y": -1.302e-4, "z": 0.0, "vortex": 0.0, "phase": 0.0},
    ]

    print(build_payload_text(build_message_from_traps(example_traps)))

    # Send a packet (will come from local port 61557, and go to 127.0.0.1:61556)
    send_traps(example_traps)

    # Optional cleanup
    close_udp_client()
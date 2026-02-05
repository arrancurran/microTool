from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple
import socket


@dataclass(frozen=True)
class SpotRow:
    """Represents one line inside <spots> ... </spots>.

    IMPORTANT: We keep this generic because we don't yet know the exact
    meaning of each column. The goal is to reproduce the wire format.
    """

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
    """Format floats in a LabVIEW-ish readable style.

    Uses scientific notation for very small/large magnitudes and fixed
    decimals otherwise, similar to typical LabVIEW formatting.
    """

    ax = abs(x)
    if (ax != 0.0) and (ax < 1e-3 or ax >= 1e4):
        return f"{x:.6E}"
    return f"{x:.6f}"


def build_payload_text(msg: UdpHoloMessage) -> str:
    """Build the textual payload for the SLM UDP protocol.

    The structure matches the <data> / <spots> / <totalA> / <blazing> /
    <zernike> / <window_rect> / <aspect> / <centre> blocks.
    """

    lines: list[str] = []
    lines.append("<data>")

    # spots block
    lines.append("<spots>")
    for s in msg.spots:
        # Space-separated columns on one line
        line = " ".join(_fmt_float(v) for v in s.cols)
        lines.append(line)
    lines.append("</spots>")

    # totalA
    lines.append("<totalA>")
    lines.append(_fmt_float(msg.totalA))
    lines.append("</totalA>")

    # blazing LUT (one float per line)
    lines.append("<blazing>")
    for v in msg.blazing:
        lines.append(_fmt_float(v))
    lines.append("</blazing>")

    # zernike coeffs (one float per line)
    lines.append("<zernike>")
    for c in msg.zernike:
        lines.append(_fmt_float(c))
    lines.append("</zernike>")

    # window rect
    x0, y0, w, h = msg.window_rect
    lines.append("<window_rect>")
    lines.append(f"{x0}, {y0}, {w}, {h},")
    lines.append("</window_rect>")

    # aspect
    ax, ay = msg.aspect
    lines.append("<aspect>")
    lines.append(f"{_fmt_float(ax)}, {_fmt_float(ay)}")
    lines.append("</aspect>")

    # centre
    cx, cy = msg.centre
    lines.append("<centre>")
    lines.append(f"{_fmt_float(cx)}, {_fmt_float(cy)}")
    lines.append("</centre>")

    lines.append("</data>")

    # LabVIEW often ends with newline; harmless and helps parsers
    return "\n".join(lines) + "\n"


def send_udp_text(host: str, port: int, payload: str) -> None:
    """Send the given text payload via UDP to (host, port)."""

    data = payload.encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(data, (host, port))


# Default SLM connection parameters; adjust as needed or override when
# calling from the UI code.
SLM_HOST: str = "127.0.0.1"
SLM_PORT: int = 5005


# Reusable defaults for fields that are not yet controlled via the UI.
DEFAULT_BLAZING: Sequence[float] = [
    0.0,
    0.061207,
    0.121163,
    0.178615,
    0.232312,
    0.281003,
    0.323435,
    0.358392,
    0.385699,
    0.406379,
    0.421520,
    0.432209,
    0.439535,
    0.444586,
    0.448449,
    0.452214,
    0.456968,
    0.463798,
    0.473794,
    0.488043,
    0.507634,
    0.533624,
    0.566254,
    0.604853,
    0.648701,
    0.697080,
    0.749270,
    0.804552,
    0.862208,
    0.921519,
    0.981766,
    1.0,
]

DEFAULT_ZERNIKE: Sequence[float] = [7.0, 0.0, -7.0] + [0.0] * 9
DEFAULT_WINDOW_RECT: Tuple[int, int, int, int] = (2560, 0, 512, 512)


def build_message_from_traps(traps: Iterable[Mapping[str, float]]) -> UdpHoloMessage:
    """Convert a collection of optical trap dicts into a UdpHoloMessage.

    Each trap mapping is expected to contain the keys
    "intensity", "x", "y", "z", "vortex", and "phase".

    We map these into a generic SpotRow.cols layout; the exact column
    semantics can be refined later to match the LabVIEW consumer.
    """

    spots: list[SpotRow] = []
    totalA = 0.0

    for t in traps:
        intensity = float(t.get("intensity", 0.0))
        x = float(t.get("x", 0.0))
        y = float(t.get("y", 0.0))
        z = float(t.get("z", 0.0))
        vortex = float(t.get("vortex", 0.0))
        phase = float(t.get("phase", 0.0))

        # Example mapping: [x, y, z, intensity, vortex, phase, 0, 0, 1]
        cols = (x, y, z, intensity, vortex, phase, 0.0, 0.0, 1.0)
        spots.append(SpotRow(cols=cols))
        totalA += intensity

    msg = UdpHoloMessage(
        spots=spots,
        totalA=totalA,
        blazing=DEFAULT_BLAZING,
        zernike=DEFAULT_ZERNIKE,
        window_rect=DEFAULT_WINDOW_RECT,
        aspect=(1.0, 1.0),
        centre=(0.5, 0.5),
    )
    return msg


def send_traps(
    traps: Iterable[Mapping[str, float]], host: str = SLM_HOST, port: int = SLM_PORT
) -> None:
    """Build and send an SLM hologram message for the given traps.

    This is the main entry point to call from the UI whenever trap
    parameters change.
    """

    msg = build_message_from_traps(traps)
    payload = build_payload_text(msg)
    send_udp_text(host, port, payload)


if __name__ == "__main__":
    # Simple self-test: build a message from two example traps and
    # print the payload. Adjust SLM_HOST/SLM_PORT if you want to
    # actually send to an SLM during development.
    example_traps = [
        {"intensity": 1.0, "x": -1.84e-4, "y": -1.86e-4, "z": 0.0, "vortex": 0.0, "phase": 0.0},
        {"intensity": 0.0, "x": -1.104e-4, "y": -1.302e-4, "z": 0.0, "vortex": 0.0, "phase": 0.0},
    ]

    msg = build_message_from_traps(example_traps)
    payload = build_payload_text(msg)
    print(payload)
    # Example send:
    # send_traps(example_traps)

"""
Standalone UDP diagnostic tool for udp_holo.py.

Use this to verify the Python sender is working *before* worrying about
whether the external (LabVIEW-driven) program receives/parses it correctly.

Typical workflow:
  1. Stop the external listening program (it's using the real port).
  2. Run this script in listen mode on that same port:
         python udp_debug_listener.py listen 61556
     It will print every packet it receives, exactly as bytes were sent.
  3. In another terminal, run udp_holo.py (or call send_traps(...) yourself)
     so it sends to 127.0.0.1:61556. Confirm the printed payload matches
     build_payload_text() output.
  4. Restart the external program and repeat with your real script to see
     if it behaves differently (e.g. no response, wrong port, firewall).

You can also use "send" mode to fire a single raw UDP payload without any
of udp_holo.py's dependencies, useful for isolating whether the problem is
in message construction or in the socket layer itself:
         python udp_debug_listener.py send 127.0.0.1 61556 "hello"
"""

from __future__ import annotations

import socket
import sys
import time


def listen(host: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    print(f"Listening on {host}:{port} (Ctrl+C to stop)...")
    try:
        while True:
            data, addr = sock.recvfrom(65535)
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] {len(data)} bytes from {addr}:")
            try:
                print(data.decode("utf-8"))
            except UnicodeDecodeError:
                print(repr(data))
            print("-" * 40)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()


def send(host: str, port: int, text: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = text.encode("utf-8")
    sock.sendto(data, (host, port))
    print(f"Sent {len(data)} bytes to {host}:{port}")
    sock.close()


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return

    mode = sys.argv[1]
    if mode == "listen":
        host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 61556
        if len(sys.argv) == 3:
            # single arg after mode treated as port on 127.0.0.1
            host, port = "127.0.0.1", int(sys.argv[2])
        listen(host, port)
    elif mode == "send":
        host = sys.argv[2]
        port = int(sys.argv[3])
        text = sys.argv[4] if len(sys.argv) > 4 else "test payload\n"
        send(host, port, text)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

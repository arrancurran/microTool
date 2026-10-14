"""Run directly, or with python -m instruments.KPC101.test_app."""

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt6.QtWidgets import QApplication
from instruments.KPC101 import KPC101
from instruments.KPC101.panel import KPC101Panel


def main():
    parser = argparse.ArgumentParser(description="Standalone KPC101 piezo test panel")
    parser.add_argument("--simulate", action="store_true", help="Use an in-memory device; no hardware access")
    parser.add_argument("--kinesis-path", help="Kinesis installation directory")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    panel = KPC101Panel(KPC101(args.kinesis_path, simulate=args.simulate))
    panel.setWindowTitle("KPC101 test app")
    panel.resize(760, 300)
    app.aboutToQuit.connect(panel.shutdown)
    panel.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

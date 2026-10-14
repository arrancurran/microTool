"""Offscreen checks for live target coalescing and background polling."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import threading
import unittest

from PyQt6.QtWidgets import QApplication

from .controller import KPC101
from .live_control import PiezoControl


class LiveControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.device = KPC101(simulate=True)
        self.device.connect("SIM-KPC101")
        self.device.enable()
        self.panel = PiezoControl(self.device)
        self.panel.timer.stop()
        self.panel._display(self.device.status())
        self.panel._buttons()

    def tearDown(self):
        self.panel.shutdown()

    def test_latest_slider_target_wins_and_readback_does_not_reset_it(self):
        for target in (100, 500, 1234):
            self.panel.slider.setValue(target)
        self.panel._display(self.device.status())
        self.assertEqual(self.panel.numeric.value(), 12.34)
        self.assertEqual(self.panel._target[1], 12.34)
        self.panel._tick()
        self.panel._future[0].result(timeout=3)
        self.assertEqual(self.device.status().voltage, 12.34)
        self.assertTrue(self.panel.slider.isEnabled())

    def test_disable_clicked_during_readback_is_queued(self):
        entered, release = threading.Event(), threading.Event()
        status = self.device.status()

        def read():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("Test did not release readback")
            return status

        self.panel._start(read, self.panel._display, background=True)
        try:
            self.assertTrue(entered.wait(3))
            self.assertTrue(self.panel.slider.isEnabled())
            self.assertTrue(self.panel.enable_button.isEnabled())
            self.panel.enable_button.click()
            self.assertIsNotNone(self.panel._queued)
        finally:
            release.set()
        self.panel._future[0].result(timeout=3)
        self.panel._tick()
        self.panel._future[0].result(timeout=3)
        self.assertFalse(self.device.status().enabled)


if __name__ == "__main__":
    unittest.main()

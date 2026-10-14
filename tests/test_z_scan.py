import tempfile
import threading
import unittest
from pathlib import Path

import h5py
import numpy as np

from acquisitions.z_scan import acquire_stack, scan_positions
from instruments.KPC101 import KPC101, Mode


class Camera:
    def __init__(self, piezo, fail_at=None):
        self.piezo = piezo
        self.running = False
        self.captures = 0
        self.fail_at = fail_at

    def start_camera(self):
        self.running = True

    def stop_camera(self):
        self.running = False

    def get_image(self):
        assert self.running
        if self.captures == self.fail_at:
            raise RuntimeError("Camera failure")
        self.captures += 1
        self.image = np.full((3, 4), round(self.piezo.status().voltage), dtype="uint16")
        return True

    def get_image_data(self):
        return self.image


class ZScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.piezo = KPC101(simulate=True)
        self.piezo.connect("SIM-KPC101")
        self.piezo.enable()

    def tearDown(self):
        self.piezo.disconnect()
        self.tmp.cleanup()

    def run_scan(self, positions, stop=None, progress=lambda *_: None, camera=None):
        return acquire_stack(camera or Camera(self.piezo), self.piezo, positions,
                             str(Path(self.tmp.name) / "test"), 0, stop or threading.Event(), progress)

    def test_positions_include_end_and_support_descending(self):
        self.assertEqual(scan_positions(0, 1, .3), [0, .3, .6, .9, 1])
        self.assertEqual(scan_positions(1, 0, .4), [1, .6, .2, 0])
        self.assertEqual(scan_positions(2, 2, 1), [2])
        for step in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                scan_positions(0, 1, step)

    def test_fresh_frames_match_z_and_metadata(self):
        filename, count = self.run_scan([0, 2, 4])
        self.assertEqual(count, 3)
        with h5py.File(filename) as file:
            np.testing.assert_array_equal(file["frames"][:, 0, 0], [0, 2, 4])
            np.testing.assert_array_equal(file["z_positions"], [0, 2, 4])
            np.testing.assert_array_equal(file["z_readback"], [0, 2, 4])
            self.assertEqual(file.attrs["Scan Status"], "complete")
            self.assertEqual(file["z_positions"].attrs["units"], "V")
            self.assertEqual(len(file["timestamps"]), 3)

    def test_stop_keeps_aligned_partial_stack(self):
        stop = threading.Event()
        filename, count = self.run_scan([0, 1, 2], stop, lambda *_: stop.set())
        self.assertEqual(count, 1)
        with h5py.File(filename) as file:
            self.assertEqual(file.attrs["Scan Status"], "cancelled")
            self.assertEqual(len(file["frames"]), len(file["z_positions"]))

    def test_failure_preserves_previous_planes_and_stops_camera(self):
        camera = Camera(self.piezo, fail_at=1)
        with self.assertRaisesRegex(RuntimeError, "Partial scan saved"):
            self.run_scan([0, 1, 2], camera=camera)
        self.assertFalse(camera.running)
        with h5py.File(next(Path(self.tmp.name).glob("*.h5"))) as file:
            self.assertEqual(file.attrs["Scan Status"], "failed")
            self.assertEqual(len(file["frames"]), 1)
            self.assertEqual(len(file["z_positions"]), 1)

    def test_rejects_out_of_range_before_creating_file(self):
        with self.assertRaises(ValueError):
            self.run_scan([0, 76])
        self.assertEqual(list(Path(self.tmp.name).glob("*.h5")), [])

    def test_closed_loop_units_and_positions(self):
        self.piezo.set_mode(Mode.CLOSED_LOOP)
        filename, _ = self.run_scan([0, 20, 40])
        with h5py.File(filename) as file:
            self.assertEqual(file.attrs["Z Units"], "percent_travel")
            np.testing.assert_array_equal(file["z_readback"], [0, 20, 40])


if __name__ == "__main__":
    unittest.main()

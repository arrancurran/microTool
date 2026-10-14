import os
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from instruments.SLM import udp_holo as udp
from instruments.noCam.noCam import NoCam, NoImage


def zernike_values(payload):
    return [float(v) for v in payload.split("<zernike>\n")[1].split("</zernike>")[0].split()]


class AberrationTests(unittest.TestCase):
    def setUp(self):
        defaults = patch.object(udp, "DEFAULT_ZERNIKE", [8.0] + [0.0]*11)
        defaults.start()
        self.addCleanup(defaults.stop)

    def test_exact_engine_order_and_fixed_zero_modes(self):
        udp.DEFAULT_ZERNIKE = [99.0]*12
        udp.set_aberration_coefficients(
            astigmatism_1=1.25, astigmatism_2=-2.5, coma_1=3.75, coma_2=-4.125
        )
        message = udp.build_message_from_traps([{"intensity": 1}])
        expected = [1.25, 0, -2.5, 0, 3.75, -4.125, 0, 0, 0, 0, 0, 0]
        self.assertEqual(zernike_values(udp.build_payload_text(message)), expected)
        udp.set_aberration_coefficients(coma_1=5)
        self.assertEqual(message.zernike, expected)
        with self.assertRaises(ValueError):
            udp.set_aberration_coefficients(coma_1=float("nan"))

    def test_each_control_resends_complete_udp_message(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        from interface.app_ui import AppUI

        app = QApplication.instance() or QApplication([])
        with patch.object(udp, "get_udp_client") as client, patch.object(AppUI, "_update_spot_markers_on_camera"):
            ui = AppUI()
            self.assertEqual(ui.aberration_spins["astigmatism_1"].value(), 8)
            expected = [8.0] + [0.0]*11
            for name, index, value in (
                ("astigmatism_1", 0, 1.25), ("astigmatism_2", 2, -2.5),
                ("coma_1", 4, 3.75), ("coma_2", 5, -4.125),
            ):
                client.return_value.write_text.reset_mock()
                ui.aberration_spins[name].setValue(value)
                client.return_value.write_text.assert_called_once()
                payload = client.return_value.write_text.call_args.args[0]
                expected[index] = value
                self.assertEqual(zernike_values(payload), expected)
                self.assertIn("<spots>", payload)
                self.assertIn("<blazing>", payload)
            ui.deleteLater()
            app.processEvents()

    def test_mock_camera_supplies_blank_frames(self):
        camera = NoCam()
        camera.open_device()
        camera.start_acquisition()
        image = NoImage()
        for width, height in ((31, 25), (16, 12)):
            camera.set_width(width)
            camera.set_height(height)
            self.assertTrue(camera.get_image(image))
            frame = image.get_image_data_numpy()
            self.assertEqual(frame.shape, (height, width))
            self.assertFalse(frame.any())

    def test_session_round_trip_restores_controls_and_udp(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        from interface.app_ui import AppUI
        from utils import last_session

        app = QApplication.instance() or QApplication([])
        camera = Mock()
        camera.call_camera_command.return_value = None
        values = dict(astigmatism_1=1.234567, astigmatism_2=-2.5, coma_1=3.75, coma_2=-4.125)
        expected = [1.234567, 0, -2.5, 0, 3.75, -4.125, 0, 0, 0, 0, 0, 0]
        with tempfile.TemporaryDirectory() as directory, patch.object(udp, "get_udp_client") as client, patch.object(AppUI, "_update_spot_markers_on_camera"), patch.object(last_session, "_SESSION_PATH", Path(directory)/"session.json"):
            first = AppUI()
            for name, value in values.items():
                first.aberration_spins[name].setValue(value)
            last_session.save_last_session(first, camera)
            saved = json.loads(last_session._SESSION_PATH.read_text())
            self.assertEqual(saved["slm_zernike"], values)
            # Simulate a fresh process with the original defaults.
            udp.DEFAULT_ZERNIKE = [8.0] + [0.0]*11
            second = AppUI()
            client.return_value.write_text.reset_mock()
            last_session.load_last_session(second, camera)
            self.assertEqual({name: spin.value() for name, spin in second.aberration_spins.items()}, values)
            calls = client.return_value.write_text.call_args_list
            self.assertTrue(calls)
            for call in calls:
                self.assertEqual(zernike_values(call.args[0]), expected)
            # A Zernike-only session also pushes the restored values to UDP.
            last_session._SESSION_PATH.write_text(json.dumps({"slm_zernike": values}))
            client.return_value.write_text.reset_mock()
            last_session.load_last_session(second, camera)
            client.return_value.write_text.assert_called_once()
            # Old sessions preserve defaults; invalid coefficients are ignored.
            last_session._SESSION_PATH.write_text(json.dumps({"slm_zernike": {"coma_1": "nan", "coma_2": None}}))
            last_session.load_last_session(second, camera)
            self.assertEqual(second.aberration_spins["coma_1"].value(), values["coma_1"])
            last_session._SESSION_PATH.write_text("{}")
            last_session.load_last_session(second, camera)
            self.assertEqual(second.aberration_spins["astigmatism_1"].value(), values["astigmatism_1"])
            first.deleteLater()
            second.deleteLater()
            app.processEvents()


if __name__ == "__main__":
    unittest.main()

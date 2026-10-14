"""Hardware-free checks: python -m unittest instruments.KPC101.test_controller."""

import unittest
from unittest.mock import Mock

from .controller import KPC101, KPCError, Mode


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.device = KPC101(simulate=True)
        self.device.connect("SIM-KPC101")

    def tearDown(self):
        self.device.disconnect()

    def test_requires_enable_and_correct_mode(self):
        with self.assertRaises(KPCError):
            self.device.set_voltage(10)
        self.device.enable()
        self.device.set_voltage(12.5)
        self.assertEqual(self.device.status().voltage, 12.5)
        with self.assertRaises(KPCError):
            self.device.set_position_percent(20)
        self.device.set_mode(Mode.CLOSED_LOOP)
        self.device.set_position_percent(20)
        self.assertEqual(self.device.status().position_percent, 20)
        with self.assertRaises(KPCError):
            self.device.set_voltage(10)

    def test_invalid_values_never_reach_output(self):
        self.device.enable()
        for value in (-1, 76, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.device.set_voltage(value)
        self.assertEqual(self.device.status().voltage, 0)

    def test_zero_blocks_moves_until_complete(self):
        self.device.enable()
        self.device.zero()
        self.assertTrue(self.device.status().zeroing)
        with self.assertRaises(KPCError):
            self.device.set_voltage(1)
        self.device._zero_until = 1
        self.assertTrue(self.device.status().zeroed)

    def test_disconnect_is_idempotent_and_preserves_output(self):
        self.device.enable()
        self.device.set_voltage(10)
        self.device.disconnect()
        self.device.disconnect()
        with self.assertRaises(KPCError):
            self.device.status()
        self.device.connect("SIM-KPC101")
        self.assertEqual(self.device.status().voltage, 10)

    def test_native_scaling_and_signedness(self):
        device = KPC101()
        device.serial = "113000001"
        dll = device._dll = Mock()
        dll.KPC_CheckConnection.return_value = True
        dll.KPC_GetStatusBits.return_value = 0x80000100
        dll.KPC_GetMaxOutputVoltage.return_value = 750
        dll.KPC_GetPositionControlMode.return_value = 1
        dll.KPC_GetOutputVoltage.return_value = 16384
        dll.KPC_SetOutputVoltage.return_value = 0
        device.set_voltage(75)
        dll.KPC_SetOutputVoltage.assert_called_once_with(b"113000001", 32767)
        self.assertAlmostEqual(device.status().voltage, 37.5, places=2)
        dll.KPC_GetPositionControlMode.return_value = 2
        dll.KPC_GetPosition.return_value = 32767
        dll.KPC_SetPosition.return_value = 0
        device.set_position_percent(100)
        dll.KPC_SetPosition.assert_called_once_with(b"113000001", 32767)
        self.assertEqual(device.status().position_percent, 100)

    def test_initial_readback_failure_closes_device(self):
        device = KPC101()
        device.discover = lambda: ["113000001"]
        dll = device._dll = Mock()
        dll.KPC_Open.return_value = 0
        dll.KPC_RequestStatus.return_value = 0
        device.status = Mock(side_effect=KPCError("Invalid configuration"))
        with self.assertRaises(KPCError):
            device.connect("113000001")
        dll.KPC_Close.assert_called_once()
        self.assertIsNone(device.serial)


if __name__ == "__main__":
    unittest.main()

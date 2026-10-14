import socket
import unittest
from unittest.mock import Mock, patch

from instruments.SLM import udp_holo as udp


class UdpTransportTests(unittest.TestCase):
    def tearDown(self):
        udp.close_udp_client()

    def test_real_loopback_and_source_port_reopen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
            receiver.bind(("127.0.0.1", 0))
            receiver.settimeout(1)
            remote_port = receiver.getsockname()[1]
            client = udp.LabviewUdpClient("127.0.0.1", 0, "127.0.0.1", remote_port)
            local_port = client.sock.getsockname()[1]
            try:
                client.write_text("first")
                data, source = receiver.recvfrom(1024)
                self.assertEqual(data, b"first")
                self.assertEqual(source[1], local_port)
            finally:
                client.close()
            client = udp.LabviewUdpClient("127.0.0.1", local_port, "127.0.0.1", remote_port)
            try:
                client.write_text("second")
                self.assertEqual(receiver.recvfrom(1024)[0], b"second")
            finally:
                client.close()

    def test_failed_initialization_closes_socket(self):
        with patch.object(udp.socket, "socket") as factory:
            factory.return_value.bind.side_effect = OSError("occupied")
            with self.assertRaises(OSError):
                udp.LabviewUdpClient("127.0.0.1", 1234, "127.0.0.1", 5678)
            factory.return_value.close.assert_called_once()

    def test_send_failure_recreates_socket_and_retries_same_payload(self):
        first, second = Mock(), Mock()
        first.write_text.side_effect = ConnectionResetError("receiver restarted")
        with patch.object(udp, "LabviewUdpClient", side_effect=[first, second]):
            udp.send_traps([{"intensity": 1}])
            first.close.assert_called_once()
            second.write_text.assert_called_once_with(first.write_text.call_args.args[0])
            self.assertIs(udp._udp_client, second)

    def test_repeated_failure_is_bounded_and_discards_socket(self):
        clients = [Mock(), Mock()]
        for client in clients:
            client.write_text.side_effect = OSError("unreachable")
        with patch.object(udp, "LabviewUdpClient", side_effect=clients) as factory:
            with self.assertRaises(OSError):
                udp.send_traps([])
            self.assertEqual(factory.call_count, 2)
            self.assertIsNone(udp._udp_client)
            for client in clients:
                client.close.assert_called_once()

    def test_oversize_message_does_not_open_socket(self):
        with patch.object(udp, "get_udp_client") as client:
            with self.assertRaises(ValueError):
                udp.send_traps([{"intensity": 1}] * 1000)
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()

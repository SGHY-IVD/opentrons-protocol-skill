"""Offline extension tests; no USB discovery, robot, or SDK simulation.

The Point stand-in verifies only the retained rotation mathematics. USB and
device peers are in-memory test doubles, not firmware or physical validation.
"""

import gc
import importlib
import math
import struct
import sys
import types
import unittest
from collections import deque, namedtuple
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "_flex_extension_tests"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "assets/python")]
sys.modules[PACKAGE] = package
transport = importlib.import_module(PACKAGE + ".communication.ch340_transport")
tilt = importlib.import_module(PACKAGE + ".devices.tilt")

Point = namedtuple("Point", "x y z")
point_types = types.ModuleType("opentrons.types")
point_types.Point = Point



class USBError(Exception):
    def __init__(self, message="timeout", errno=110):
        super().__init__(message)
        self.errno = errno


class Endpoint:
    def __init__(self, address):
        self.bEndpointAddress = address
        self.wMaxPacketSize = 32
        self.pending = deque()
        self.writes = []

    def read(self, size, timeout):
        if not self.pending:
            raise USBError()
        value = self.pending.popleft()
        if isinstance(value, BaseException):
            raise value
        return value

    def write(self, value, timeout):
        self.writes.append(bytes(value))
        return len(value)


class USBDevice:
    def __init__(self, address=1, ports=(1,), fail=False):
        self.bus, self.address, self.port_numbers = 1, address, ports
        self.events = []
        self.input, self.output = Endpoint(0x81), Endpoint(0x02)
        self.fail = fail

    def is_kernel_driver_active(self, interface):
        return True

    def detach_kernel_driver(self, interface):
        self.events.append("detach")

    def attach_kernel_driver(self, interface):
        self.events.append("attach")

    def set_configuration(self):
        self.events.append("configure")

    def ctrl_transfer(self, *args):
        self.events.append(args)
        if self.fail:
            raise USBError("setup failed", errno=5)

    def get_active_configuration(self):
        return {(0, 0): [self.output, self.input]}

    def clear_halt(self, address):
        pass


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.core = types.SimpleNamespace(USBError=USBError, find=lambda **kw: [])
        self.util = types.SimpleNamespace(
            ENDPOINT_IN=0x80, ENDPOINT_OUT=0,
            endpoint_direction=lambda address: address & 0x80,
            find_descriptor=lambda endpoints, custom_match:
                next((e for e in endpoints if custom_match(e)), None),
            claim_interface=lambda d, i: d.events.append("claim"),
            release_interface=lambda d, i: d.events.append("release"),
            dispose_resources=lambda d: d.events.append("dispose"),
        )
        self.environment = patch.multiple(transport, PYUSB_AVAILABLE=True,
                                          usb_core=self.core, usb_util=self.util)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def opened(self, device):
        instance = transport.PyUsbCH340Transport(device)
        instance.open()
        self.addCleanup(instance.close)
        return instance

    def test_import_and_construction_never_discover_or_connect(self):
        with patch.object(self.core, "find", side_effect=AssertionError("USB access")):
            importlib.reload(tilt)
            self.assertFalse(transport.PyUsbCH340Transport().is_open)
            self.assertFalse(tilt.TiltDevice().connected)

    def test_selection_requires_unambiguous_physical_device(self):
        first = dict(bus=1, address=1, port_numbers=(1,), device=object())
        second = dict(bus=1, address=2, port_numbers=(2,), device=object())
        with self.assertRaises(transport.TransportError):
            transport.select_ch340_usb([first, second])
        self.assertIs(transport.select_ch340_usb(
            [first, second], usb_bus=1, usb_port_numbers=(2,)), second)
        with self.assertRaises(transport.TransportError):
            transport.select_ch340_usb([first], usb_address=9)

    def test_initialization_preserves_source_control_transfers(self):
        device = USBDevice()
        self.opened(device)
        self.assertEqual([e for e in device.events if isinstance(e, tuple)], [
            (0x40, 0xA1, 0, 0), (0x40, 0x9A, 0x1312, 0xCC83),
            (0x40, 0x9A, 0x2518, 0x00C3), (0x40, 0xA4, 0x00FF, 0),
        ])

    def test_byte_transport_has_no_device_frame_requirement(self):
        device = USBDevice()
        instance = self.opened(device)
        self.assertEqual(instance.write(b"DIY\x01"), 4)
        self.assertEqual(device.output.writes, [b"DIY\x01"])
        device.input.pending.append(b"arbitrary-five-byte-reply")
        self.assertEqual(instance.read(5), b"arbit")
        self.assertEqual(instance.read(4), b"rary")
        self.assertEqual(instance.read(100), b"-five-byte-reply")

    def test_timeout_is_empty_but_other_usb_errors_propagate(self):
        device = USBDevice()
        instance = self.opened(device)
        self.assertEqual(instance.read(3), b"")
        device.input.pending.append(USBError("disconnected", errno=19))
        with self.assertRaises(USBError):
            instance.read(3)

    def test_invalid_read_sizes_and_zero_read_do_not_consume_input(self):
        for value in [0, -1, math.nan, True]:
            with self.assertRaises(ValueError):
                transport.PyUsbCH340Transport(usb_timeout_ms=value)
        device = USBDevice()
        instance = self.opened(device)
        device.input.pending.append(b"abc")
        for size in [-1, 1.5, True]:
            with self.assertRaises(ValueError):
                instance.read(size)
        self.assertEqual(instance.read(0), b"")
        self.assertEqual(instance.read(3), b"abc")

    def test_continuous_input_cannot_hold_buffer_reset_forever(self):
        device = USBDevice()
        instance = self.opened(device)
        device.input.pending.extend([b"still-streaming"] * 4)
        with patch.object(transport.time, "monotonic", side_effect=[0, 0.1, 0.3]):
            with self.assertRaises(transport.TransportError):
                instance.reset_input_buffer()

    def test_live_owner_cannot_be_released_by_another_instance(self):
        device = USBDevice()
        owner = self.opened(device)
        rejected = transport.PyUsbCH340Transport(device)
        with self.assertRaises(transport.TransportError):
            rejected.open()
        rejected.close()
        self.assertTrue(owner.is_open)
        self.assertNotIn("release", device.events)
        self.assertEqual(transport.clear_stale_ch340_usb_handles(), 0)

    def test_distinct_devices_can_be_open_together(self):
        first = self.opened(USBDevice())
        second = self.opened(USBDevice(2, (2,)))
        first.close()
        self.assertTrue(second.is_open)

    def test_initialization_failure_restores_driver_and_allows_retry(self):
        device = USBDevice(fail=True)
        instance = transport.PyUsbCH340Transport(device)
        with self.assertRaises(transport.TransportError):
            instance.open()
        self.assertIn("release", device.events)
        self.assertIn("attach", device.events)
        self.assertFalse(instance.interface_claimed)
        self.assertFalse(instance._detached_kernel_driver)
        device.fail = False
        instance.dev = device
        instance.open()
        instance.close()
        instance.close()
        self.assertFalse(instance.is_open)

    def test_lost_owner_reclaims_only_the_same_physical_device(self):
        device = USBDevice()
        abandoned = transport.PyUsbCH340Transport(device)
        abandoned.open()
        del abandoned
        gc.collect()
        replacement = self.opened(device)
        self.assertTrue(replacement.stale_handle_released)
        self.assertEqual(device.events.count("release"), 1)


def response(payload=b""):
    body = payload.ljust(62, b"\0")
    return body + struct.pack(">H", tilt.crc16_modbus(body))


class DevicePeer:
    """In-memory command peer with source-format replies and partial reads."""
    def __init__(self):
        self.is_open = True
        self.angle, self.state = 0.0, 0
        self.sent = []
        self.buffer = bytearray()
        self.chunk_size = 7
        self.short_write = False
        self.corrupt_command = None
        self.silence_command = None
        self.result = 0

    def close(self):
        self.is_open = False

    def reset_input_buffer(self):
        self.buffer.clear()

    def reset_output_buffer(self):
        pass

    def flush(self):
        pass

    def write(self, request):
        command = struct.unpack_from("<H", request)[0]
        self.sent.append(command)
        if self.short_write:
            return len(request) - 1
        if command == 30001:
            self.state, self.angle = 0, 0.0
        elif command == 30002:
            self.angle = struct.unpack_from("<f", request, 2)[0]
        elif command == 30003:
            self.angle += struct.unpack_from("<f", request, 2)[0]
        payload = (struct.pack("<Bf", self.state, self.angle) if command == 30004
                   else bytes([self.result]) if command >= 30001 else b"")
        frame = response(payload)
        if command == self.corrupt_command:
            frame = frame[:-1] + bytes([frame[-1] ^ 1])
        self.buffer.extend(b"" if command == self.silence_command else frame)
        return len(request)

    def read(self, size):
        count = min(size, self.chunk_size, len(self.buffer))
        value = bytes(self.buffer[:count])
        del self.buffer[:count]
        return value


class DeviceTests(unittest.TestCase):
    def make_controller(self, **kwargs):
        controller = tilt.TiltController(**kwargs)
        peer = DevicePeer()
        controller.transport = peer
        return controller, peer

    def test_source_wire_anchor_and_crc_rejection(self):
        frame = tilt.build_frame(0)
        self.assertEqual(frame, b"\0" * 62 + b"\xab\x01")
        payload = struct.pack("<ff", -12.5, 2)
        self.assertEqual(tilt.build_frame(30002, payload)[2:10], payload)
        with self.assertRaises(ValueError):
            tilt.parse_response_frame(frame[:-1] + b"\x02")
        with self.assertRaises(ValueError):
            tilt.build_frame(1, b"x" * 61)

    def test_partial_reads_and_real_command_volume_are_accumulated(self):
        controller, peer = self.make_controller()
        self.assertEqual(controller.get_status()["state"], 0)
        self.assertEqual(peer.sent, [30004])
        self.assertTrue(controller.communication_verified)

    def test_unknown_status_and_nonfinite_angle_never_send_motion(self):
        for state, angle in [(255, 0), (0, math.nan), (0, math.inf)]:
            with self.subTest(state=state, angle=angle):
                controller, peer = self.make_controller()
                peer.state, peer.angle = state, angle
                with self.assertRaises(tilt.TiltStateError):
                    controller.move_absolute(5, 2)
                self.assertNotIn(30002, peer.sent)

    def test_configured_bounds_cannot_be_nan_or_nonpositive(self):
        for key in ["max_angle_deg", "max_speed_deg_s"]:
            for value in [math.nan, math.inf, 0, -1]:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    tilt.TiltController(**{key: value})

    def test_fault_moving_and_unhomed_device_states_block_motion(self):
        for state in [1, 2, 3]:
            controller, peer = self.make_controller()
            peer.state = state
            with self.assertRaises(tilt.TiltStateError):
                controller.move_relative(1, 2)
            self.assertNotIn(30003, peer.sent)

    def test_reported_ready_state_does_not_force_session_home(self):
        controller, peer = self.make_controller()
        device = tilt.TiltDevice()
        device.controller = controller
        self.assertFalse(device.homed)
        self.assertAlmostEqual(device.move_to(12).angle_deg, 12)
        self.assertAlmostEqual(device.move_by(-5).angle_deg, 7)
        self.assertNotIn(30001, peer.sent)

    def test_home_and_explicit_calibration_preserve_command_semantics(self):
        controller, peer = self.make_controller()
        device = tilt.TiltDevice()
        device.controller = controller
        self.assertTrue(device.home().is_idle)
        self.assertTrue(device.homed)
        self.assertTrue(device.calibrate_zero().is_idle)
        self.assertEqual(peer.sent.count(30001), 1)
        self.assertEqual(peer.sent.count(30005), 1)

    def test_failed_crc_or_partial_write_closes_uncertain_connection(self):
        for failure in ["corrupt_command", "short_write"]:
            controller, peer = self.make_controller()
            setattr(peer, failure, 30004 if failure == "corrupt_command" else True)
            with self.assertRaises((ValueError, tilt.TiltCommunicationError)):
                controller.get_status()
            self.assertFalse(controller.connected)
            self.assertFalse(controller.communication_verified)

    def test_lost_motion_reply_is_not_replayed_and_invalidates_cache(self):
        controller, peer = self.make_controller(response_timeout=0.001)
        device = tilt.TiltDevice()
        device.controller = controller
        device.status()
        peer.silence_command = 30002
        with self.assertRaises(tilt.TiltTimeoutError):
            device.move_to(5, timeout=0.001)
        self.assertEqual(peer.sent.count(30002), 1)
        self.assertFalse(device.connected)
        self.assertIsNone(device.last_status)

    def test_connect_import_dependencies_and_handshake_do_not_move(self):
        controller, peer = self.make_controller()
        controller.transport = None
        peer.is_open = False
        peer.open = lambda: setattr(peer, "is_open", True)
        selected = {"device": object(), "bus": 1, "address": 2,
                    "port_numbers": (2,)}
        with patch.multiple(tilt, PYUSB_AVAILABLE=True,
                            enumerate_ch340_usb=lambda: [selected],
                            PyUsbCH340Transport=lambda device: peer):
            device = tilt.TiltDevice()
            connection = device.open()
            self.assertTrue(connection.status.is_idle)
            self.assertEqual(peer.sent, [0, 20, 30004])
            device.close()
            self.assertFalse(device.connected)

    def test_first_ping_timeout_reconnects_before_read_only_retry(self):
        device = tilt.TiltDevice(response_timeout=0.001)
        first, second = DevicePeer(), DevicePeer()
        first.silence_command = 0
        # Advance only the silent peer's virtual clock. A real 1 ms deadline
        # can expire during the healthy peer's fragmented response under load.
        clock = [0.0]
        first_read = first.read

        def silent_read(size):
            clock[0] += 0.002
            return first_read(size)

        first.read = silent_read
        first.is_open = second.is_open = False
        first.open = lambda: setattr(first, "is_open", True)
        second.open = lambda: setattr(second, "is_open", True)
        peers = iter([first, second])
        selected = {"device": object(), "bus": 1, "address": 2,
                    "port_numbers": (2,)}
        with patch.multiple(tilt, PYUSB_AVAILABLE=True,
                            enumerate_ch340_usb=lambda: [selected],
                            PyUsbCH340Transport=lambda device: next(peers)), \
                patch.object(tilt.time, "sleep"), \
                patch.object(tilt.time, "monotonic", lambda: clock[0]):
            self.assertTrue(device.open().status.is_idle)
        self.assertFalse(first.is_open)
        self.assertEqual(first.sent, [0])
        self.assertEqual(second.sent, [0, 20, 30004])
        self.assertFalse(device.homed)
        device.close()

    def test_failed_ping_hides_old_session_snapshots(self):
        controller, peer = self.make_controller(response_timeout=0.001)
        device = tilt.TiltDevice()
        device.controller = controller
        device.home()
        device._device_info = {"raw_payload_hex": "00"}
        self.assertTrue(device.homed)
        self.assertIsNotNone(device.last_status)
        peer.silence_command = 0
        with self.assertRaises(tilt.TiltTimeoutError):
            device.ping()
        self.assertFalse(device.connected)
        self.assertFalse(device.homed)
        self.assertIsNone(device.last_status)
        self.assertIsNone(device.device_info)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(sys.modules, {
            "opentrons": types.ModuleType("opentrons"),
            "opentrons.types": point_types,
        })
        environment.start()
        self.addCleanup(environment.stop)

    def test_axis_rotation_direction_inverse_and_distance(self):
        model = tilt.TiltGeometry(axis_x=4, axis_z=8)
        point = Point(7, 2, 12)
        self.assertEqual(model.rotate(point, 0), point)
        self.assertEqual(model.rotate(Point(4, 2, 8), 90), Point(4, 2, 8))
        at_90 = model.rotate(Point(5, 2, 8), 90)
        self.assertAlmostEqual(at_90.x, 4)
        self.assertAlmostEqual(at_90.z, 7)
        for angle in [-30, -12.5, 0, 25, 90]:
            rotated = model.rotate(point, angle)
            restored = model.rotate(rotated, -angle)
            self.assertEqual(rotated.y, point.y)
            self.assertAlmostEqual(math.hypot(rotated.x - 4, rotated.z - 8), 5)
            for actual, expected in zip(restored, point):
                self.assertAlmostEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()

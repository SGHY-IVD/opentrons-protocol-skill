"""Offline regression tests of the standalone positive-pressure extension.

Only the generated positive_pressure.py is copied to an isolated directory.
Real PyUSB and Opentrons imports are blocked; commands, USB setup and ownership
are exercised with memory peers. These tests do not validate firmware, pressure
units or limits, robot motion, physical clearance, or actual USB hardware.
"""

import builtins
import importlib.util
import math
import re
import shutil
import sys
import tempfile
import types
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "assets/python/devices/positive_pressure.py"
TILT_TARGET = ROOT / "assets/python/devices/tilt.py"
PRACTICES = ROOT / "references/module-practices-positive-pressure.md"


class ImportGuard:
    """The standalone file must import without installed USB or robot SDK."""

    def __init__(self):
        self.usb_attempts = []
        self.sdk_attempts = []
        self.original = builtins.__import__

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        if name == "usb" or name.startswith("usb."):
            self.usb_attempts.append(name)
            raise ImportError("real USB blocked in offline positive-pressure tests")
        if name == "opentrons" or name.startswith("opentrons."):
            self.sdk_attempts.append(name)
            raise AssertionError("unexpected robot SDK import: " + name)
        if level:
            raise AssertionError("standalone file used a relative import")
        return self.original(name, globals, locals, fromlist, level)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def advance(self, seconds=0.1):
        self.now += seconds

    def sleep(self, seconds):
        self.advance(seconds)


class MemoryTransport:
    """No real waiting; optional virtual time advances on every read."""

    def __init__(self, chunks=(), *, clock=None, tick=0.1, continuous=None):
        self.is_open = False
        self.chunks = deque(chunks)
        self.clock, self.tick, self.continuous = clock, tick, continuous
        self.opens = self.closes = self.resets = self.reads = 0
        self.writes = []
        self.write_result = None
        self.write_error = None
        self.open_error = None
        self.reset_error = None

    def open(self):
        self.opens += 1
        if self.open_error is not None:
            raise self.open_error
        self.is_open = True

    def close(self):
        self.closes += 1
        self.is_open = False

    def reset_input_buffer(self):
        self.resets += 1
        if self.reset_error is not None:
            raise self.reset_error

    def write(self, data):
        self.writes.append(bytes(data))
        if self.write_error is not None:
            raise self.write_error
        return len(data) if self.write_result is None else self.write_result

    def read(self, size):
        self.reads += 1
        if self.reads > 500:
            raise AssertionError("response loop has no finite total deadline")
        if self.clock is not None:
            self.clock.advance(self.tick)
        value = self.chunks.popleft() if self.chunks else self.continuous or b""
        if isinstance(value, BaseException):
            raise value
        if len(value) > size:
            self.chunks.appendleft(value[size:])
        return value[:size]


class ContextDouble:
    def __init__(self, simulating=True, dry_run=False):
        self.simulating, self.dry_run = simulating, dry_run
        self.params = types.SimpleNamespace(dry_run=dry_run)
        self.comments, self.delays = [], []

    def is_simulating(self):
        return self.simulating

    def comment(self, value):
        self.comments.append(value)

    def delay(self, *args, **kwargs):
        self.delays.append((args, kwargs))


class GripperContextDouble(ContextDouble):
    """Record only the SDK call contract; no robot geometry is simulated."""

    def __init__(self, simulating=True, observe_move=None):
        super().__init__(simulating=simulating)
        self.moves = []
        self.observe_move = observe_move

    def move_labware(self, labware, new_location, **kwargs):
        self.moves.append((labware, new_location, dict(kwargs)))
        if self.observe_move is not None:
            self.observe_move()
        labware.location = new_location


class USBError(Exception):
    def __init__(self, message="timeout", errno=110):
        super().__init__(message)
        self.errno = errno


class Endpoint:
    def __init__(self, address):
        self.bEndpointAddress, self.wMaxPacketSize = address, 32
        self.writes, self.read_calls = [], []

    def read(self, size, timeout):
        self.read_calls.append((size, timeout))
        raise USBError()

    def write(self, data, timeout):
        self.writes.append((bytes(data), timeout))
        return len(data)


class USBDevice:
    def __init__(self, address=1, ports=(1,), fail_setup=False):
        self.bus, self.address, self.port_numbers = 1, address, ports
        self.fail_setup = fail_setup
        self.events = []
        self.input, self.output = Endpoint(0x81), Endpoint(0x02)

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
        if self.fail_setup:
            raise USBError("synthetic setup failure", errno=5)

    def get_active_configuration(self):
        return {(0, 0): [self.output, self.input]}

    def clear_halt(self, address):
        self.events.append(("clear_halt", address))


class PositivePressureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="standalone-ppm-test-")
        self.addCleanup(self.temp.cleanup)
        self.ppm, self.import_guard = self.load_standalone(TARGET, "positive_pressure")
        # Keep real USB and SDK inaccessible throughout every memory-only test.
        self.guard = ImportGuard()
        guard_patch = patch("builtins.__import__", self.guard)
        guard_patch.start()
        self.addCleanup(guard_patch.stop)

    def load_standalone(self, source, stem):
        isolated = Path(self.temp.name) / (stem + ".py")
        shutil.copyfile(source, isolated)
        module_name = "_isolated_ppm_test_" + stem
        spec = importlib.util.spec_from_file_location(module_name, isolated)
        module = importlib.util.module_from_spec(spec)
        modules_patch = patch.dict(sys.modules, {module_name: module})
        modules_patch.start()
        self.addCleanup(modules_patch.stop)
        guard = ImportGuard()
        with patch("builtins.__import__", guard):
            spec.loader.exec_module(module)
        return module, guard

    def controller(self, chunks=(b"ok\r\n",), **kwargs):
        peer = MemoryTransport(chunks)
        controller = self.ppm.PPMController(transport=peer, **kwargs)
        self.addCleanup(controller.close)
        return controller, peer

    def ticking_controller(self, chunks=(), *, continuous=None, tick=0.1, **kwargs):
        clock = FakeClock()
        peer = MemoryTransport(chunks, clock=clock, tick=tick, continuous=continuous)
        controller = self.ppm.PPMController(transport=peer, **kwargs)
        self.addCleanup(controller.close)
        time_patch = patch.multiple(self.ppm.time, monotonic=clock.monotonic, sleep=clock.sleep)
        time_patch.start()
        self.addCleanup(time_patch.stop)
        controller.connect()
        return controller, peer, clock

    def fake_usb(self, *modules, devices=()):
        discoveries = []

        def find(**kwargs):
            discoveries.append(kwargs)
            return list(devices)

        core = types.SimpleNamespace(USBError=USBError, find=find)
        util = types.SimpleNamespace(
            ENDPOINT_IN=0x80, ENDPOINT_OUT=0,
            endpoint_direction=lambda address: address & 0x80,
            find_descriptor=lambda endpoints, custom_match:
                next((item for item in endpoints if custom_match(item)), None),
            claim_interface=lambda device, interface: device.events.append("claim"),
            release_interface=lambda device, interface: device.events.append("release"),
            dispose_resources=lambda device: device.events.append("dispose"),
        )
        for module in modules:
            environment = patch.multiple(module, PYUSB_AVAILABLE=True, usb_core=core, usb_util=util)
            environment.start()
            self.addCleanup(environment.stop)
        return core, discoveries

    def practice_examples(self, peer):
        """Execute the current fenced examples, never a copied test version."""
        heading = "# 第三方正压模块"
        text = PRACTICES.read_text()
        self.assertEqual(text.count(heading), 1)
        section = text.split(heading, 1)[1]
        snippets = re.findall(r"```python\s*\n(.*?)```", section, flags=re.S)
        self.assertEqual(len(snippets), 3, "positive-pressure examples changed; review their coverage")
        devices = []

        def device_factory(context):
            instance = self.ppm.PPMDevice(context, transport=peer, response_timeout=0.2)
            devices.append(instance)
            self.addCleanup(instance.close)
            return instance

        namespace = {"PPMDevice": device_factory}
        for index, snippet in enumerate(snippets, 1):
            exec(compile(snippet, f"{PRACTICES}:positive-pressure-example-{index}", "exec"), namespace)
        self.assertTrue({"positive_pressure_example", "positive_pressure_reset_example",
                         "positive_pressure_transfer_example"}.issubset(namespace))
        return namespace, devices

    def transfer_settings(self):
        return {
            "pressure_slot": "B4", "return_slot": "C1",
            "source_pick_up_offset": {"x": 1, "y": 2, "z": 3},
            "pressure_drop_offset": {"x": 4, "y": 5, "z": 6},
            "pressure_pick_up_offset": {"x": 7, "y": 8, "z": 9},
            "destination_drop_offset": {"x": 10, "y": 11, "z": 12},
            "pressure_kpa": 8, "seconds": 0.125,
        }

    def test_single_file_import_and_construction_do_not_touch_hardware_or_sdk(self):
        self.assertEqual(self.ppm.__package__, "")
        self.assertEqual(self.import_guard.sdk_attempts, [])
        self.assertTrue(issubclass(self.ppm.PPMDevice, self.ppm.PPMController))
        with patch.object(self.ppm, "enumerate_ch340_usb", side_effect=AssertionError("discovery during construction")), \
                patch.object(self.ppm.PressureCH340Transport, "open", side_effect=AssertionError("open during construction")):
            controller = self.ppm.PPMController()
            device = self.ppm.PPMDevice(ContextDouble(simulating=False))
        self.assertFalse(controller.connected)
        self.assertFalse(device.connected)
        self.assertEqual(self.guard.sdk_attempts, [])

    def test_command_encoding_is_source_compatible_and_never_added_reset(self):
        controller, peer = self.controller((b"ok\r\n", b"ok\n"))
        controller.connect()
        self.assertIsNone(controller.send_pressure_time(0, 1))
        self.assertIsNone(controller.reset_x_and_z())
        self.assertEqual(peer.writes, [b"C 0 1 0 0\r\n", b"D\r\n"])
        self.assertTrue(controller.connected)
        self.assertIn("ok", controller.last_response)

    def test_integer_valued_numbers_and_no_unproven_vendor_cap(self):
        controller, peer = self.controller((b"ok\n", b"ok\n"))
        controller.connect()
        controller.send_pressure_time(2.0, 1200.0)
        controller.send_pressure_time(100000, 10000000)
        self.assertEqual(peer.writes, [b"C 2 1200 0 0\r\n", b"C 100000 10000000 0 0\r\n"])

    def test_connect_and_close_are_idempotent_and_do_not_issue_commands(self):
        controller, peer = self.controller()
        controller.connect()
        controller.connect()
        self.assertEqual(peer.opens, 1)
        self.assertTrue(controller.connected)
        controller.disconnect()
        controller.close()
        self.assertFalse(controller.connected)
        self.assertEqual(peer.writes, [])

    def test_command_requires_explicit_connection(self):
        controller, peer = self.controller()
        for action in (lambda: controller.send_pressure_time(1, 100), controller.reset_x_and_z):
            with self.assertRaises(RuntimeError):
                action()
        self.assertEqual((peer.opens, peer.resets, peer.reads, peer.writes), (0, 0, 0, []))

    def test_fragmented_ack_echo_and_busy_share_one_stream(self):
        controller, peer = self.controller((b"C 8 100 0 0\r", b"\necho:bu", b"sy\r\no", b"k\r", b"\n"))
        controller.connect()
        controller.send_pressure_time(8, 100)
        self.assertEqual(peer.writes, [b"C 8 100 0 0\r\n"])
        self.assertTrue(controller.connected)

    def test_ack_strips_surrounding_whitespace(self):
        controller, _ = self.controller((b" \tok \t\r\n",))
        controller.connect()
        controller.send_pressure_time(2, 1)
        self.assertTrue(controller.connected)

    def test_substrings_or_uppercase_never_count_as_ack(self):
        for wrong_ack in (b"not ok\n", b"token:ok\r\n", b"ok extra\n", b"OK\n", b"book\n"):
            with self.subTest(response=wrong_ack):
                controller, peer, _ = self.ticking_controller((wrong_ack,), response_timeout=0.2)
                with self.assertRaises(RuntimeError):
                    controller.send_pressure_time(1, 1)
                self.assertFalse(controller.connected)
                self.assertEqual(len(peer.writes), 1)
                self.assertEqual(peer.closes, 1)

    def test_incomplete_ack_without_newline_times_out(self):
        controller, peer, _ = self.ticking_controller((b"ok",), response_timeout=0.2)
        with self.assertRaises(RuntimeError):
            controller.send_pressure_time(1, 1)
        self.assertFalse(controller.connected)
        self.assertEqual(peer.writes, [b"C 1 1 0 0\r\n"])

    def test_no_ack_has_finite_deadline_and_no_automatic_replay_or_reset(self):
        controller, peer, clock = self.ticking_controller(response_timeout=0.2)
        with self.assertRaises(RuntimeError):
            controller.send_pressure_time(1, 1)
        self.assertGreaterEqual(clock.now, 0.2)
        self.assertLess(clock.now, 1.0)
        self.assertEqual(peer.writes, [b"C 1 1 0 0\r\n"])
        self.assertFalse(controller.connected)
        self.assertEqual(peer.closes, 1)

    def test_continuous_busy_cannot_restart_total_deadline(self):
        controller, peer, clock = self.ticking_controller(continuous=b"echo:busy\r\n", response_timeout=0.3)
        with self.assertRaises(RuntimeError):
            controller.send_pressure_time(1, 1)
        self.assertLess(clock.now, 1.0)
        self.assertLess(peer.reads, 20)
        self.assertEqual(peer.writes, [b"C 1 1 0 0\r\n"])
        self.assertFalse(controller.connected)

    def test_pressure_deadline_includes_requested_duration(self):
        controller, peer, clock = self.ticking_controller(
            (b"echo:busy\n", b"echo:busy\n", b"echo:busy\n", b"ok\n"),
            response_timeout=0.2, tick=0.4,
        )
        controller.send_pressure_time(1, 2000)
        self.assertGreater(clock.now, 0.2)
        self.assertTrue(controller.connected)
        self.assertEqual(len(peer.writes), 1)

    def test_reset_uses_its_own_finite_timeout(self):
        controller, peer, clock = self.ticking_controller(
            continuous=b"echo:busy\n", response_timeout=10, reset_timeout=0.2,
        )
        with self.assertRaises(RuntimeError):
            controller.reset_x_and_z()
        self.assertLess(clock.now, 1.0)
        self.assertEqual(peer.writes, [b"D\r\n"])

    def test_short_write_is_uncertain_failure_closes_without_replay(self):
        controller, peer = self.controller()
        peer.write_result = 2
        controller.connect()
        with self.assertRaises(RuntimeError):
            controller.send_pressure_time(5, 300)
        self.assertEqual(peer.writes, [b"C 5 300 0 0\r\n"])
        self.assertEqual(peer.reads, 0)
        self.assertEqual(peer.closes, 1)
        self.assertFalse(controller.connected)

    def test_transport_write_and_read_failures_close_without_extra_commands(self):
        for stage in ("write", "read", "reset"):
            with self.subTest(stage=stage):
                controller, peer = self.controller()
                controller.connect()
                if stage == "write":
                    peer.write_error = RuntimeError("uncertain write")
                elif stage == "read":
                    peer.chunks = deque([RuntimeError("uncertain read")])
                else:
                    peer.reset_error = RuntimeError("cannot drain input")
                with self.assertRaises(RuntimeError):
                    controller.send_pressure_time(5, 300)
                self.assertEqual(peer.writes, [] if stage == "reset" else [b"C 5 300 0 0\r\n"])
                self.assertEqual(peer.closes, 1)
                self.assertFalse(controller.connected)

    def test_failed_open_cleans_up_without_commands(self):
        controller, peer = self.controller()
        peer.open_error = RuntimeError("synthetic open failure")
        with self.assertRaises(RuntimeError):
            controller.connect()
        self.assertFalse(controller.connected)
        self.assertEqual(peer.writes, [])
        self.assertGreaterEqual(peer.closes, 1)

    def test_invalid_utf8_is_not_silently_removed_to_forge_ack(self):
        controller, peer = self.controller((b"\xffok\n",))
        controller.connect()
        with self.assertRaises(RuntimeError):
            controller.send_pressure_time(1, 100)
        self.assertFalse(controller.connected)
        self.assertEqual(len(peer.writes), 1)

    def test_unbounded_line_and_response_are_rejected(self):
        for kwargs, data in (({"max_line_bytes": 8}, b"x" * 9),
                             ({"max_line_bytes": 8, "max_response_bytes": 12}, b"noise\nnoise\nnoise\n")):
            with self.subTest(kwargs=kwargs):
                controller, peer, _ = self.ticking_controller((data,), response_timeout=0.2, **kwargs)
                with self.assertRaisesRegex(RuntimeError, next(iter(kwargs)) if len(kwargs) == 1 else "max_response_bytes"):
                    controller.send_pressure_time(1, 1)
                self.assertFalse(controller.connected)
                self.assertEqual(len(peer.writes), 1)

    def test_buffered_duplicate_ack_cannot_acknowledge_the_next_command(self):
        controller, peer, _ = self.ticking_controller((b"ok\nok\n",), response_timeout=0.2)
        controller.send_pressure_time(1, 1)
        with self.assertRaises(RuntimeError):
            controller.send_pressure_time(2, 1)
        self.assertEqual(peer.writes, [b"C 1 1 0 0\r\n", b"C 2 1 0 0\r\n"])
        self.assertFalse(controller.connected)

    def test_context_manager_only_connects_and_closes_without_reset(self):
        controller, peer = self.controller()
        with controller as entered:
            self.assertIs(entered, controller)
            self.assertTrue(controller.connected)
        self.assertFalse(controller.connected)
        self.assertEqual(peer.writes, [])
        self.assertEqual((peer.opens, peer.closes), (1, 1))

    def test_overflowing_duration_is_rejected_before_any_side_effect(self):
        controller, peer = self.controller()
        controller.connect()
        before = (peer.opens, peer.closes, peer.resets, peer.reads, list(peer.writes))
        with self.assertRaises((TypeError, ValueError)):
            controller.send_pressure_time(1, 10 ** 1000)
        self.assertEqual((peer.opens, peer.closes, peer.resets, peer.reads, peer.writes), before)
        self.assertTrue(controller.connected)

    def test_invalid_millisecond_arguments_have_no_side_effects(self):
        invalid = (True, False, None, "1", -1, 0.5, math.nan, math.inf, -math.inf)
        for value in invalid:
            for connected in (False, True):
                with self.subTest(value=value, connected=connected):
                    controller, peer = self.controller()
                    if connected:
                        controller.connect()
                    before = (peer.opens, peer.closes, peer.resets, peer.reads, list(peer.writes))
                    with self.assertRaises((TypeError, ValueError)):
                        controller.send_pressure_time(value, 1)
                    with self.assertRaises((TypeError, ValueError)):
                        controller.send_pressure_time(1, value)
                    self.assertEqual((peer.opens, peer.closes, peer.resets, peer.reads, peer.writes), before)
                    self.assertEqual(controller.connected, connected)
        controller, peer = self.controller()
        with self.assertRaises((TypeError, ValueError)):
            controller.send_pressure_time(1, 0)
        self.assertEqual(peer.writes, [])

    def test_invalid_constructor_limits_are_rejected_before_open(self):
        for name in ("response_timeout", "reset_timeout"):
            for value in (True, 0, -1, math.nan, math.inf, "1"):
                with self.subTest(name=name, value=value):
                    peer = MemoryTransport()
                    with self.assertRaises((TypeError, ValueError)):
                        self.ppm.PPMController(transport=peer, **{name: value})
                    self.assertEqual((peer.opens, peer.closes, peer.writes), (0, 0, []))
        for name in ("usb_timeout_ms", "max_line_bytes", "max_response_bytes"):
            for value in (True, 0, -1, 0.5):
                with self.subTest(name=name, value=value):
                    with self.assertRaises((TypeError, ValueError)):
                        self.ppm.PPMController(transport=MemoryTransport(), **{name: value})

    def test_device_seconds_convert_once_and_truncate_fractional_milliseconds(self):
        peer = MemoryTransport((b"ok\n", b"ok\n"))
        context = ContextDouble(simulating=False)
        device = self.ppm.PPMDevice(context, transport=peer)
        self.addCleanup(device.close)
        device.connect()
        device.send_pressure_time(4, 1.2349)
        device.send_pressure_time(4, 0.001)
        self.assertEqual(peer.writes, [b"C 4 1234 0 0\r\n", b"C 4 1 0 0\r\n"])
        self.assertTrue(context.comments)

    def test_official_simulation_uses_no_transport_or_real_sleep(self):
        context = ContextDouble(simulating=True)
        peer = MemoryTransport()
        device = self.ppm.PPMDevice(context, transport=peer)
        with patch.object(self.ppm.time, "sleep", side_effect=AssertionError("real sleep during SDK simulation")), \
                patch.object(self.ppm, "enumerate_ch340_usb", side_effect=AssertionError("USB during SDK simulation")):
            device.connect()
            device.reset_x_and_z()
            device.send_pressure_time(2, 1.2349)
            device.disconnect()
        self.assertEqual((peer.opens, peer.closes, peer.resets, peer.reads, peer.writes), (0, 0, 0, 0, []))
        self.assertTrue(context.comments)
        self.assertTrue(context.delays)

    def test_official_simulation_preserves_source_operations_without_connection(self):
        context = ContextDouble(simulating=True)
        peer = MemoryTransport()
        device = self.ppm.PPMDevice(context, transport=peer)
        device.reset_x_and_z()
        device.send_pressure_time(0, 0.01)
        self.assertEqual((peer.opens, peer.closes, peer.resets, peer.reads, peer.writes), (0, 0, 0, 0, []))
        self.assertEqual(context.delays, [((), {"seconds": 0.01})])

    def test_simulation_and_hardware_apply_identical_input_validation_first(self):
        invalid_pressure = (True, "1", -1, 0.1, math.nan, math.inf)
        invalid_seconds = (True, "1", 0, -1, 0.0009, math.nan, math.inf, 1e308)
        for simulating in (True, False):
            context = ContextDouble(simulating=simulating)
            peer = MemoryTransport()
            device = self.ppm.PPMDevice(context, transport=peer)
            for pressure in invalid_pressure:
                with self.subTest(simulating=simulating, pressure=pressure):
                    with self.assertRaises((TypeError, ValueError)):
                        device.send_pressure_time(pressure, 1)
            for seconds in invalid_seconds:
                with self.subTest(simulating=simulating, seconds=seconds):
                    with self.assertRaises((TypeError, ValueError)):
                        device.send_pressure_time(1, seconds)
            self.assertEqual((peer.opens, peer.closes, peer.resets, peer.reads, peer.writes), (0, 0, 0, 0, []))
            self.assertEqual(context.comments, [])
            self.assertEqual(context.delays, [])

    def test_custom_dry_run_flag_does_not_disable_real_hardware_backend(self):
        context = ContextDouble(simulating=False, dry_run=True)
        peer = MemoryTransport((b"ok\n",))
        device = self.ppm.PPMDevice(context, transport=peer)
        self.addCleanup(device.close)
        device.connect()
        device.send_pressure_time(2, 0.1)
        self.assertEqual(peer.opens, 1)
        self.assertEqual(peer.writes, [b"C 2 100 0 0\r\n"])

    def test_pressure_usb_setup_retains_exact_three_source_transfers(self):
        device = USBDevice()
        self.fake_usb(self.ppm)
        transport = self.ppm.PressureCH340Transport(device)
        self.addCleanup(transport.close)
        transport.open()
        transfers = [event for event in device.events if isinstance(event, tuple) and event[0] == 0x40]
        self.assertEqual(transfers, [(0x40, 0xA1, 0, 0),
                                     (0x40, 0x9A, 0x2518, 0x00C3),
                                     (0x40, 0xA4, 0xFF, 0)])
        self.assertNotIn((0x40, 0x9A, 0x1312, 0xCC83), transfers)
        self.assertTrue(transport.is_open)
        self.assertIn("claim", device.events)

    def test_multiple_ch340_rejected_without_claim_and_explicit_selector_works(self):
        devices = [USBDevice(address=1, ports=(1,)), USBDevice(address=2, ports=(2,))]
        _, discoveries = self.fake_usb(self.ppm, devices=devices)
        ambiguous = self.ppm.PPMController()
        self.addCleanup(ambiguous.close)
        with self.assertRaises(RuntimeError):
            ambiguous.connect()
        self.assertFalse(ambiguous.connected)
        self.assertTrue(discoveries)
        for device in devices:
            self.assertNotIn("configure", device.events)
            self.assertNotIn("claim", device.events)
        selected = self.ppm.PPMController(usb_bus=1, usb_port_numbers=(2,))
        self.addCleanup(selected.close)
        selected.connect()
        self.assertTrue(selected.connected)
        self.assertNotIn("configure", devices[0].events)
        self.assertIn("configure", devices[1].events)

    def test_ppm_and_tilt_share_physical_device_ownership(self):
        tilt, _ = self.load_standalone(TILT_TARGET, "tilt")
        self.fake_usb(self.ppm, tilt)
        device = USBDevice()
        tilt_owner = tilt.PyUsbCH340Transport(device)
        self.addCleanup(tilt_owner.close)
        tilt_owner.open()
        pressure = self.ppm.PressureCH340Transport(device)
        self.addCleanup(pressure.close)
        before = list(device.events)
        with self.assertRaises(RuntimeError):
            pressure.open()
        self.assertFalse(pressure.is_open)
        self.assertEqual(device.events, before)
        pressure.close()
        self.assertEqual(device.events, before)
        self.assertTrue(tilt_owner.is_open)
        tilt_owner.close()
        pressure = self.ppm.PressureCH340Transport(device)
        self.addCleanup(pressure.close)
        pressure.open()
        self.assertTrue(pressure.is_open)
        second_tilt = tilt.PyUsbCH340Transport(device)
        self.addCleanup(second_tilt.close)
        with self.assertRaises(RuntimeError):
            second_tilt.open()
        self.assertTrue(pressure.is_open)

    def test_different_physical_pressure_devices_can_be_open_concurrently(self):
        self.fake_usb(self.ppm)
        first = self.ppm.PressureCH340Transport(USBDevice(address=1, ports=(1,)))
        second = self.ppm.PressureCH340Transport(USBDevice(address=2, ports=(2,)))
        self.addCleanup(first.close)
        self.addCleanup(second.close)
        first.open()
        second.open()
        self.assertTrue(first.is_open)
        self.assertTrue(second.is_open)
        first.close()
        self.assertTrue(second.is_open)

    def test_failed_usb_setup_releases_claim_and_allows_later_owner(self):
        device = USBDevice(fail_setup=True)
        self.fake_usb(self.ppm)
        failed = self.ppm.PressureCH340Transport(device)
        self.addCleanup(failed.close)
        with self.assertRaises(RuntimeError):
            failed.open()
        self.assertFalse(failed.is_open)
        self.assertIn("release", device.events)
        self.assertIn("dispose", device.events)
        self.assertIn("attach", device.events)
        device.fail_setup = False
        recovered = self.ppm.PressureCH340Transport(device)
        self.addCleanup(recovered.close)
        recovered.open()
        self.assertTrue(recovered.is_open)

    def test_live_practice_single_pressure_in_hardware_and_official_simulation(self):
        for simulating in (False, True):
            with self.subTest(simulating=simulating):
                peer = MemoryTransport((b"ok\r\n",))
                examples, devices = self.practice_examples(peer)
                context = ContextDouble(simulating=simulating)
                examples["positive_pressure_example"](context, pressure_kpa=8, seconds=0.125)
                self.assertEqual(len(devices), 1)
                self.assertFalse(devices[0].connected)
                self.assertTrue(context.comments)
                if simulating:
                    self.assertEqual((peer.opens, peer.closes, peer.writes), (0, 0, []))
                    self.assertEqual(context.delays, [((), {"seconds": 0.125})])
                else:
                    self.assertEqual((peer.opens, peer.closes), (1, 1))
                    self.assertEqual(peer.writes, [b"C 8 125 0 0\r\n"])
                    self.assertEqual(context.delays, [])

    def test_live_practice_reset_in_hardware_and_official_simulation(self):
        for simulating in (False, True):
            with self.subTest(simulating=simulating):
                peer = MemoryTransport((b"ok\n",))
                examples, devices = self.practice_examples(peer)
                context = ContextDouble(simulating=simulating)
                examples["positive_pressure_reset_example"](context)
                self.assertEqual(len(devices), 1)
                self.assertFalse(devices[0].connected)
                self.assertTrue(context.comments)
                self.assertEqual(context.delays, [])
                if simulating:
                    self.assertEqual((peer.opens, peer.closes, peer.writes), (0, 0, []))
                else:
                    self.assertEqual((peer.opens, peer.closes), (1, 1))
                    self.assertEqual(peer.writes, [b"D\r\n"])

    def test_live_practice_gripper_roundtrip_in_hardware_and_official_simulation(self):
        for simulating in (False, True):
            with self.subTest(simulating=simulating):
                peer = MemoryTransport((b"ok\n",))
                examples, devices = self.practice_examples(peer)
                move_observations = []
                context = GripperContextDouble(
                    simulating=simulating,
                    observe_move=lambda: move_observations.append((peer.is_open, list(peer.writes))),
                )
                assembly = types.SimpleNamespace(location="C1")
                settings = self.transfer_settings()
                examples["positive_pressure_transfer_example"](context, assembly, **settings)
                self.assertEqual(context.moves, [
                    (assembly, "B4", {"use_gripper": True,
                                      "pick_up_offset": settings["source_pick_up_offset"],
                                      "drop_offset": settings["pressure_drop_offset"]}),
                    (assembly, "C1", {"use_gripper": True,
                                      "pick_up_offset": settings["pressure_pick_up_offset"],
                                      "drop_offset": settings["destination_drop_offset"]}),
                ])
                self.assertEqual(assembly.location, "C1")
                self.assertEqual(len(devices), 1)
                self.assertFalse(devices[0].connected)
                self.assertEqual(move_observations[0], (False, []))
                if simulating:
                    self.assertEqual((peer.opens, peer.closes, peer.writes), (0, 0, []))
                    self.assertEqual(move_observations[1], (False, []))
                    self.assertEqual(context.delays, [((), {"seconds": 0.125})])
                else:
                    self.assertEqual((peer.opens, peer.closes), (1, 1))
                    self.assertEqual(peer.writes, [b"C 8 125 0 0\r\n"])
                    self.assertEqual(move_observations[1], (False, [b"C 8 125 0 0\r\n"]))
                    self.assertEqual(context.delays, [])

    def test_live_practice_pressure_failure_closes_without_return_move_or_reset(self):
        for failure in ("write", "read"):
            with self.subTest(failure=failure):
                peer = MemoryTransport((RuntimeError("synthetic pressure response failure"),))
                if failure == "write":
                    peer.write_error = RuntimeError("synthetic pressure write failure")
                examples, devices = self.practice_examples(peer)
                context = GripperContextDouble(simulating=False)
                assembly = types.SimpleNamespace(location="C1")
                settings = self.transfer_settings()
                with self.assertRaises(RuntimeError):
                    examples["positive_pressure_transfer_example"](context, assembly, **settings)
                self.assertEqual(context.moves, [
                    (assembly, "B4", {"use_gripper": True,
                                      "pick_up_offset": settings["source_pick_up_offset"],
                                      "drop_offset": settings["pressure_drop_offset"]}),
                ])
                self.assertEqual(assembly.location, "B4")
                self.assertEqual(peer.writes, [b"C 8 125 0 0\r\n"])
                self.assertEqual((peer.opens, peer.closes), (1, 1))
                self.assertEqual(len(devices), 1)
                self.assertFalse(devices[0].connected)
                self.assertEqual(context.delays, [])


if __name__ == "__main__":
    unittest.main()

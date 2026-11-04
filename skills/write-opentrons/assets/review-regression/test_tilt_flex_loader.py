"""Offline tests of the delivered, standalone tilt loading facade.

The actual generated tilt.py is copied away from its source tree and imported
with spec_from_file_location. USB imports are blocked and SDK operations use
small in-memory doubles. These tests verify API composition, bookkeeping and
geometry arithmetic, not the Opentrons SDK, robot motion or physical clearance.
"""

import builtins
import importlib.util
import inspect
import math
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from collections import namedtuple
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "assets/python/devices/tilt.py"
BUILD = ROOT / "scripts/build_tilt.py"
Point = namedtuple("Point", "x y z")


class LocationDouble:
    def __init__(self, point, labware):
        self.point = point
        self.labware = labware

    def move(self, offset):
        return LocationDouble(
            Point(self.point.x + offset.x, self.point.y + offset.y,
                  self.point.z + offset.z), self.labware,
        )


class WellDouble:
    def __init__(self, name, x, y, z, depth=10):
        self.name = name
        self.point = Point(x, y, z)
        self.depth = depth

    def bottom(self, z=0):
        return LocationDouble(
            Point(self.point.x, self.point.y, self.point.z + z), self,
        )

    def center(self):
        return self.bottom(z=self.depth / 2)

    def top(self, z=0):
        return self.bottom(z=self.depth + z)


class LabwareDouble:
    def __init__(self, location="B2", load_name="memory_plate", label=None):
        self.location = location
        self.load_name = load_name
        self.label = label
        self._wells = {
            "A1": WellDouble("A1", 10, 20, 3),
            "A12": WellDouble("A12", 110, 20, 3),
        }

    def wells(self):
        return list(self._wells.values())

    def wells_by_name(self):
        return dict(self._wells)


class ProtocolDouble:
    def __init__(self, simulating=True):
        self.simulating = simulating
        self.loads = []
        self.moves = []
        self.fail_next_move = False

    def is_simulating(self):
        return self.simulating

    def load_labware(self, load_name, location, label=None):
        labware = LabwareDouble(location, load_name, label)
        self.loads.append(labware)
        return labware

    def move_labware(self, labware, new_location, **kwargs):
        self.moves.append((labware, new_location, kwargs))
        if self.fail_next_move:
            self.fail_next_move = False
            raise RuntimeError("synthetic SDK move failure")
        labware.location = new_location


class ImportGuard:
    """Prevent real USB/SDK loading, while allowing our explicit SDK doubles."""

    def __init__(self, sdk_modules=None):
        self.sdk_modules = sdk_modules or {}
        self.sdk_attempts = []
        self.usb_attempts = []
        self.original = builtins.__import__

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        if name == "usb" or name.startswith("usb."):
            self.usb_attempts.append(name)
            raise ImportError("real USB is unavailable in offline loader tests")
        if name == "opentrons" or name.startswith("opentrons."):
            self.sdk_attempts.append(name)
            if name not in self.sdk_modules:
                raise AssertionError("unexpected real SDK import: " + name)
            if sys.modules.get(name) is not self.sdk_modules[name]:
                raise AssertionError("SDK double is not installed: " + name)
        if level:
            raise AssertionError("standalone bundle used a relative import")
        return self.original(name, globals, locals, fromlist, level)


class TiltFlexLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="standalone-tilt-test-")
        self.addCleanup(self.temp.cleanup)
        isolated = Path(self.temp.name) / "tilt.py"
        shutil.copyfile(TARGET, isolated)
        self.module_name = "_isolated_tilt_flex_loader_test"
        spec = importlib.util.spec_from_file_location(self.module_name, isolated)
        self.tilt = importlib.util.module_from_spec(spec)
        # dataclass/typing inspect the import registry; no package is installed.
        self.modules_patch = patch.dict(sys.modules, {self.module_name: self.tilt})
        self.modules_patch.start()
        self.addCleanup(self.modules_patch.stop)
        import_guard = ImportGuard()
        with patch("builtins.__import__", import_guard):
            spec.loader.exec_module(self.tilt)
        self.assertEqual(import_guard.sdk_attempts, [])
        self.assertEqual(self.tilt.__package__, "")

        self.off_deck = object()
        opentrons = types.ModuleType("opentrons")
        opentrons.__path__ = []
        sdk_types = types.ModuleType("opentrons.types")
        sdk_types.Point, sdk_types.Location = Point, LocationDouble
        sdk_protocol = types.ModuleType("opentrons.protocol_api")
        sdk_protocol.OFF_DECK = self.off_deck
        opentrons.types, opentrons.protocol_api = sdk_types, sdk_protocol
        self.sdk_modules = {
            "opentrons": opentrons, "opentrons.types": sdk_types,
            "opentrons.protocol_api": sdk_protocol,
        }
        sdk_patch = patch.dict(sys.modules, self.sdk_modules)
        sdk_patch.start()
        self.addCleanup(sdk_patch.stop)
        self.guard = ImportGuard(self.sdk_modules)
        guard_patch = patch("builtins.__import__", self.guard)
        guard_patch.start()
        self.addCleanup(guard_patch.stop)
        # A regression selecting hardware must fail before any discovery/open.
        for owner, name in (
            (self.tilt, "enumerate_ch340_usb"),
            (self.tilt.TiltDevice, "open"),
            (self.tilt.PyUsbCH340Transport, "open"),
        ):
            usb_patch = patch.object(
                owner, name, side_effect=AssertionError("unexpected USB access"),
            )
            usb_patch.start()
            self.addCleanup(usb_patch.stop)

    def config(self, **overrides):
        values = {
            "location": "C2", "module_height_mm": 20.0,
            "axis_to_plate_bottom_mm": 4.0,
            "plate_bottom_to_well_bottom_mm": 1.0,
            "geometry_angle_sign": 1.0,
        }
        values.update(overrides)
        return self.tilt.TiltFlexConfig(**values)

    def ready(self, *, context=None, config=None):
        context = context or ProtocolDouble()
        module = self.tilt.load_tilt_module(context, config or self.config())
        module.connect()
        module.home()
        return context, module

    def assertPointAlmostEqual(self, actual, expected):
        for axis in ("x", "y", "z"):
            self.assertAlmostEqual(getattr(actual, axis), getattr(expected, axis))

    def test_public_bundle_api_and_required_explicit_geometry(self):
        for name in (
            "TiltFlexConfig", "TiltPose", "SimulatedTiltBackend",
            "PyUsbTiltBackend", "TiltFlexModule", "TiltPlate", "load_tilt_module",
        ):
            self.assertTrue(hasattr(self.tilt, name), name)
        for name in ("TiltPipette", "TiltGate"):
            self.assertFalse(hasattr(self.tilt, name), name)
        required = {
            "location", "module_height_mm", "axis_to_plate_bottom_mm",
            "plate_bottom_to_well_bottom_mm", "geometry_angle_sign",
        }
        signature = inspect.signature(self.tilt.TiltFlexConfig)
        for name in required:
            self.assertIs(signature.parameters[name].default, inspect.Parameter.empty)
        self.assertTrue(required.issubset({field.name for field in fields(self.config())}))
        self.assertIsNone(self.config().gripper_drop_z_mm)
        self.assertIsNone(self.config().gripper_pick_up_z_mm)
        self.assertNotIn("confirm", inspect.signature(self.tilt.TiltDevice.calibrate_zero).parameters)
        self.assertNotIn("confirm", inspect.signature(self.tilt.TiltFlexModule.calibrate_zero).parameters)

    def test_loading_only_constructs_and_selects_simulation_without_usb(self):
        for simulating, enabled in ((True, True), (True, False), (False, False)):
            with self.subTest(simulating=simulating, hardware_enabled=enabled):
                context = ProtocolDouble(simulating=simulating)
                with patch.object(
                    self.tilt, "PyUsbTiltBackend",
                    side_effect=AssertionError("simulation constructed hardware backend"),
                ):
                    module = self.tilt.load_tilt_module(
                        context, self.config(hardware_enabled=enabled),
                    )
                    self.assertIsInstance(module._backend, self.tilt.SimulatedTiltBackend)
                    self.assertFalse(module.connected)
                    self.assertFalse(module.pose.valid)
                    self.assertFalse(module.homed)
                    self.assertIsNone(module.child)
                    self.assertEqual(context.loads, [])
                    self.assertEqual(context.moves, [])
                    module.connect()
                    module.home()
                    module.set_angle(5)
                    module.level()
                    module.disconnect()
        self.assertEqual(self.guard.usb_attempts, [])

    def test_hardware_backend_construction_never_connects_or_loads_sdk(self):
        module = self.tilt.load_tilt_module(
            ProtocolDouble(simulating=False), self.config(hardware_enabled=True),
        )
        self.assertIsInstance(module._backend, self.tilt.PyUsbTiltBackend)
        self.assertFalse(module.connected)
        self.assertEqual(self.guard.sdk_attempts, [])
        self.assertEqual(self.guard.usb_attempts, [])

    def test_simulated_lifecycle_requires_explicit_home_and_disconnect_does_not_move(self):
        context = ProtocolDouble()
        module = self.tilt.load_tilt_module(context, self.config())
        with self.assertRaises(self.tilt.TiltStateError):
            module.status()
        with self.assertRaises(self.tilt.TiltStateError):
            module.home()
        self.assertTrue(module.connect().needs_home)
        self.assertFalse(module.pose.valid)
        self.assertIsNotNone(module.device_info)
        with self.assertRaises(self.tilt.TiltStateError):
            module.set_angle(8)
        self.assertTrue(module.home().is_idle)
        self.assertTrue(module.homed)
        self.assertTrue(module.pose.valid)
        self.assertEqual(module.set_angle(8).angle_deg, 8)
        self.assertEqual(module.change_angle(-3).angle_deg, 5)
        self.assertEqual(module.status().angle_deg, 5)
        self.assertEqual(module.level().angle_deg, 0)
        module.set_angle(6)
        with patch.object(module._backend, "set_angle", wraps=module._backend.set_angle) as move:
            with patch.object(module._backend, "home", wraps=module._backend.home) as home:
                module.disconnect()
                move.assert_not_called()
                home.assert_not_called()
        self.assertEqual(module.angle, 6)
        self.assertFalse(module.pose.valid)
        self.assertFalse(module.homed)
        self.assertIsNone(module.device_info)
        module.connect()
        self.assertFalse(module.pose.valid)
        self.assertFalse(module.homed)
        module.home()
        self.assertTrue(module.pose.valid)

    def test_context_manager_disconnects_even_after_exception(self):
        module = self.tilt.load_tilt_module(ProtocolDouble(), self.config())
        with self.assertRaisesRegex(RuntimeError, "caller failure"):
            with module as entered:
                self.assertIs(entered, module)
                module.home()
                module.set_angle(4)
                raise RuntimeError("caller failure")
        self.assertFalse(module.connected)
        self.assertFalse(module.pose.valid)
        self.assertEqual(module.angle, 4)

    def test_only_one_plate_loads_and_loading_requires_level_homed_module(self):
        context = ProtocolDouble()
        module = self.tilt.load_tilt_module(context, self.config())
        module.connect()
        with self.assertRaises(self.tilt.TiltStateError):
            module.load_labware("memory_plate")
        self.assertEqual(context.loads, [])
        module.home()
        module.set_angle(2)
        with self.assertRaises(self.tilt.TiltStateError):
            module.load_labware("memory_plate")
        self.assertEqual(context.loads, [])
        module.level()
        plate = module.load_labware("memory_plate", label="倾斜板")
        self.assertIs(module.child, plate)
        self.assertIs(module.tilt_plate, plate)
        self.assertEqual((plate.labware.location, plate.labware.label), ("C2", "倾斜板"))
        with self.assertRaises(self.tilt.TiltStateError):
            module.load_labware("second_plate")
        with self.assertRaises(self.tilt.TiltStateError):
            module.move_labware_onto_module(LabwareDouble(), use_gripper=False)
        self.assertEqual(len(context.loads), 1)
        self.assertEqual(context.moves, [])

    def test_level_coordinate_methods_apply_translation_and_preserve_well_metadata(self):
        _, module = self.ready(config=self.config(module_offset_x_mm=2, module_offset_y_mm=3))
        plate = module.load_labware("memory_plate")
        bottom = plate.bottom("A1", z=1, x=2, y=3)
        self.assertPointAlmostEqual(bottom.point, Point(14, 26, 24))
        self.assertIs(bottom.labware, plate.labware.wells_by_name()["A1"])
        self.assertPointAlmostEqual(plate.center("A1", z=2).point, Point(12, 23, 30))
        self.assertPointAlmostEqual(plate.top("A1", z=-1).point, Point(12, 23, 32))
        self.assertPointAlmostEqual(
            plate.location("A1", origin="bottom", x=2, y=3, z=1).point,
            bottom.point,
        )
        with self.assertRaises(KeyError):
            plate.bottom("missing")
        with self.assertRaises(ValueError):
            plate.location("A1", origin="unknown")
        with self.assertRaises(ValueError):
            plate.bottom("A1", x=math.nan)

    def test_rotation_uses_explicit_axis_sign_and_local_offsets_before_rotation(self):
        _, module = self.ready(config=self.config(
            module_offset_x_mm=2, module_offset_y_mm=3, geometry_angle_sign=-1,
        ))
        plate = module.load_labware("memory_plate")
        module.set_angle(30)
        self.assertEqual(module.pose.hardware_angle_deg, 30)
        self.assertEqual(module.pose.geometry_angle_deg, -30)
        # Axis (62, 18); translated local point (14, 26, 24). At -30 degrees,
        # dx=-48 and dz=6 give x=59-24*sqrt(3), z=-6+3*sqrt(3).
        result = plate.bottom("A1", z=1, x=2, y=3)
        self.assertPointAlmostEqual(
            result.point, Point(59 - 24 * math.sqrt(3), 26, -6 + 3 * math.sqrt(3)),
        )
        self.assertAlmostEqual(plate.geometry.axis_x, 62)
        self.assertAlmostEqual(plate.geometry.axis_z, 18)

    def test_motion_invalidates_pose_before_backend_and_success_restores_it(self):
        _, module = self.ready()
        module.load_labware("memory_plate")
        for method, invoke in (
            ("home", lambda: module.home()),
            ("set_angle", lambda: module.set_angle(7)),
            ("change_angle", lambda: module.change_angle(2)),
            ("set_angle", lambda: module.level()),
        ):
            with self.subTest(method=method):
                previous_revision = module.pose.revision
                actual = getattr(module._backend, method)

                def observe(*args, **kwargs):
                    self.assertFalse(module.pose.valid)
                    return actual(*args, **kwargs)

                with patch.object(module._backend, method, side_effect=observe) as motion:
                    invoke()
                    motion.assert_called_once()
                self.assertTrue(module.pose.valid)
                self.assertTrue(module.homed)
                self.assertGreater(module.pose.revision, previous_revision)

    def test_failed_motion_loses_pose_until_new_home_even_if_idle_status_returns(self):
        for method, invoke in (
            ("home", lambda m: m.home()),
            ("set_angle", lambda m: m.set_angle(7)),
            ("change_angle", lambda m: m.change_angle(2)),
            ("set_angle", lambda m: m.level()),
            ("calibrate_zero", lambda m: m.calibrate_zero()),
        ):
            with self.subTest(method=method):
                _, module = self.ready()
                plate = module.load_labware("memory_plate")
                module.set_angle(5)

                def fail(*args, **kwargs):
                    self.assertFalse(module.pose.valid)
                    raise RuntimeError("synthetic tilt motion failure")

                with patch.object(module._backend, method, side_effect=fail):
                    with self.assertRaisesRegex(RuntimeError, "synthetic tilt motion"):
                        invoke(module)
                self.assertFalse(module.pose.valid)
                self.assertFalse(module.homed)
                with self.assertRaises(self.tilt.TiltStateError):
                    plate.bottom("A1")
                self.assertTrue(module.status().is_idle)
                self.assertFalse(module.pose.valid)
                module.home()
                self.assertTrue(module.pose.valid)
                plate.bottom("A1")

    def test_uncertain_completion_and_status_failure_do_not_restore_pose(self):
        _, module = self.ready()
        plate = module.load_labware("memory_plate")
        invalid_results = (
            self.tilt.TiltStatus(1, "moving", 7),
            self.tilt.TiltStatus(0, "idle", 6),
            self.tilt.TiltStatus(0, "idle", math.nan),
        )
        for result in invalid_results:
            with self.subTest(result=result):
                with patch.object(module._backend, "set_angle", return_value=result):
                    with self.assertRaises(self.tilt.TiltStateError):
                        module.set_angle(7)
                self.assertFalse(module.pose.valid)
                self.assertFalse(module.homed)
                module.home()
        with patch.object(module._backend, "status", side_effect=RuntimeError("status lost")):
            with self.assertRaisesRegex(RuntimeError, "status lost"):
                module.status()
        self.assertFalse(module.pose.valid)
        with self.assertRaises(self.tilt.TiltStateError):
            plate.top("A1")

    def test_calibration_is_not_home_and_clears_geometric_reference(self):
        _, module = self.ready()
        plate = module.load_labware("memory_plate")
        module.set_angle(8)
        with patch.object(module._backend, "home", wraps=module._backend.home) as home:
            actual = module._backend.calibrate_zero

            def calibrate():
                self.assertFalse(module.pose.valid)
                return actual()

            with patch.object(module._backend, "calibrate_zero", side_effect=calibrate) as write:
                self.assertEqual(module.calibrate_zero().angle_deg, 0)
                write.assert_called_once_with()
            home.assert_not_called()
        self.assertFalse(module.homed)
        self.assertFalse(module.pose.valid)
        self.assertEqual(module.status().angle_deg, 0)
        self.assertFalse(module.pose.valid)
        with self.assertRaises(self.tilt.TiltStateError):
            plate.bottom("A1")
        with self.assertRaises(self.tilt.TiltStateError):
            module.set_angle(5)
        module.home()
        self.assertTrue(module.homed)
        self.assertTrue(module.pose.valid)
        plate.bottom("A1")

    def test_gripper_offsets_apply_to_correct_legs_and_old_plate_detaches(self):
        context, module = self.ready(config=self.config(
            gripper_drop_x_mm=1, gripper_drop_y_mm=2, gripper_drop_z_mm=13,
            gripper_pick_up_x_mm=4, gripper_pick_up_y_mm=5, gripper_pick_up_z_mm=17,
        ))
        labware = LabwareDouble(location="B2")
        source_pickup = {"x": 8, "y": 9, "z": 10}
        destination_drop = {"x": 11, "y": 12, "z": 14}
        plate = module.move_labware_onto_module(
            labware, source_pick_up_offset=source_pickup,
        )
        self.assertIs(module.child, plate)
        self.assertEqual(labware.location, "C2")
        result = module.move_labware_off_module(
            "D2", destination_drop_offset=destination_drop,
        )
        self.assertIs(result, labware)
        self.assertEqual(context.moves, [
            (labware, "C2", {
                "use_gripper": True, "pick_up_offset": source_pickup,
                "drop_offset": {"x": 1, "y": 2, "z": 13},
            }),
            (labware, "D2", {
                "use_gripper": True, "pick_up_offset": {"x": 4, "y": 5, "z": 17},
                "drop_offset": destination_drop,
            }),
        ])
        self.assertEqual(labware.location, "D2")
        self.assertIsNone(module.child)
        self.assertFalse(plate.attached)
        replacement = module.load_labware("replacement")
        self.assertIs(module.child, replacement)
        for coordinate in (plate.bottom, plate.center, plate.top, plate.location):
            with self.assertRaises(self.tilt.TiltStateError):
                coordinate("A1")

    def test_missing_measured_gripper_z_fails_before_move_without_changing_occupancy(self):
        context, module = self.ready()
        labware = LabwareDouble(location="B2")
        with self.assertRaisesRegex(ValueError, "gripper_drop_z_mm"):
            module.move_labware_onto_module(labware)
        self.assertEqual(context.moves, [])
        self.assertEqual(labware.location, "B2")
        self.assertIsNone(module.child)
        plate = module.move_labware_onto_module(labware, use_gripper=False)
        context.moves.clear()
        with self.assertRaisesRegex(ValueError, "gripper_pick_up_z_mm"):
            module.move_labware_off_module("D2")
        self.assertEqual(context.moves, [])
        self.assertIs(module.child, plate)
        self.assertTrue(plate.attached)
        self.assertEqual(labware.location, "C2")

    def test_manual_moves_require_no_gripper_offsets(self):
        context, module = self.ready()
        labware = LabwareDouble()
        module.move_labware_onto_module(labware, use_gripper=False)
        module.move_labware_off_module("D2", use_gripper=False)
        self.assertEqual(context.moves, [
            (labware, "C2", {"use_gripper": False}),
            (labware, "D2", {"use_gripper": False}),
        ])

    def test_successful_sdk_load_with_failed_plate_view_keeps_recoverable_occupancy(self):
        context, module = self.ready()
        labware = LabwareDouble(location="C2")
        labware._wells.clear()

        def load_empty_labware(load_name, location, label=None):
            self.assertEqual(location, "C2")
            context.loads.append(labware)
            return labware

        with patch.object(context, "load_labware", side_effect=load_empty_labware):
            with self.assertRaises(ValueError):
                module.load_labware("empty_plate")
        self.assertIs(module.labware, labware)
        self.assertIsNone(module.child)
        self.assertFalse(module.pose.valid)
        self.assertFalse(module.homed)
        module.home()
        with self.assertRaises(self.tilt.TiltStateError):
            module.load_labware("replacement")
        with self.assertRaises(self.tilt.TiltStateError):
            module.move_labware_onto_module(LabwareDouble(), use_gripper=False)
        self.assertEqual(len(context.loads), 1)
        self.assertEqual(context.moves, [])
        # A failed explicit removal must retain that occupancy even without a
        # coordinate view; the caller can re-home and explicitly remove it.
        context.fail_next_move = True
        with self.assertRaisesRegex(RuntimeError, "SDK move failure"):
            module.unload_labware()
        self.assertIs(module.labware, labware)
        self.assertEqual(labware.location, "C2")
        self.assertFalse(module.pose.valid)
        module.home()
        self.assertIs(module.unload_labware(), labware)
        self.assertIs(labware.location, self.off_deck)
        self.assertIsNone(module.labware)
        self.assertIsNone(module.child)
        replacement = module.load_labware("replacement")
        self.assertIs(module.labware, replacement.labware)

    def test_successful_sdk_move_onto_with_failed_view_keeps_recoverable_occupancy(self):
        context, module = self.ready()
        labware = LabwareDouble(location="B2")
        labware._wells.clear()
        with self.assertRaises(ValueError):
            module.move_labware_onto_module(labware, use_gripper=False)
        self.assertEqual(labware.location, "C2")
        self.assertIs(module.labware, labware)
        self.assertIsNone(module.child)
        self.assertFalse(module.pose.valid)
        self.assertFalse(module.homed)
        self.assertEqual(context.moves, [(labware, "C2", {"use_gripper": False})])
        module.home()
        with self.assertRaises(self.tilt.TiltStateError):
            module.load_labware("replacement")
        with self.assertRaises(self.tilt.TiltStateError):
            module.move_labware_onto_module(LabwareDouble(), use_gripper=False)
        self.assertEqual(context.loads, [])
        self.assertEqual(len(context.moves), 1)
        context.fail_next_move = True
        with self.assertRaisesRegex(RuntimeError, "SDK move failure"):
            module.move_labware_off_module("D2", use_gripper=False)
        self.assertIs(module.labware, labware)
        self.assertEqual(labware.location, "C2")
        self.assertFalse(module.pose.valid)
        module.home()
        self.assertIs(module.move_labware_off_module("D2", use_gripper=False), labware)
        self.assertEqual(labware.location, "D2")
        self.assertIsNone(module.labware)
        self.assertIsNone(module.child)

    def test_level_and_labware_moves_use_geometry_angle_with_calibration_offset(self):
        for sign, level_hardware_angle in ((1, -5), (-1, 5)):
            with self.subTest(geometry_angle_sign=sign):
                context, module = self.ready(config=self.config(
                    geometry_angle_sign=sign, geometry_angle_offset_deg=5,
                ))
                self.assertEqual(module.angle, 0)
                self.assertEqual(module.pose.geometry_angle_deg, 5)
                with self.assertRaises(self.tilt.TiltStateError):
                    module.load_labware("memory_plate")
                with self.assertRaises(self.tilt.TiltStateError):
                    module.move_labware_onto_module(LabwareDouble(), use_gripper=False)
                self.assertEqual(context.loads, [])
                self.assertEqual(context.moves, [])
                self.assertEqual(module.level().angle_deg, level_hardware_angle)
                self.assertEqual(module.pose.geometry_angle_deg, 0)
                self.assertTrue(module.pose.valid)
                plate = module.load_labware("memory_plate")
                self.assertPointAlmostEqual(plate.bottom("A1").point, Point(10, 20, 23))
                # The hardware zero can be geometrically tilted after a measured
                # zero offset. Removing a plate must use the same level check.
                module.set_angle(0)
                with self.assertRaises(self.tilt.TiltStateError):
                    module.unload_labware()
                with self.assertRaises(self.tilt.TiltStateError):
                    module.move_labware_off_module("D2", use_gripper=False)
                self.assertEqual(context.moves, [])
                self.assertIs(module.child, plate)
                module.level()
                self.assertIs(module.move_labware_off_module("D2", use_gripper=False), plate.labware)

    def test_level_target_respects_hardware_angle_boundary_before_backend_motion(self):
        for sign in (1, -1):
            with self.subTest(geometry_angle_sign=sign, target="outside limit"):
                _, module = self.ready(config=self.config(
                    geometry_angle_sign=sign, geometry_angle_offset_deg=5,
                    max_angle_deg=4,
                ))
                with patch.object(module._backend, "set_angle", wraps=module._backend.set_angle) as move:
                    with self.assertRaises(self.tilt.TiltOutOfRangeError):
                        module.level()
                    move.assert_not_called()
                self.assertEqual(module.angle, 0)
            with self.subTest(geometry_angle_sign=sign, target="at limit"):
                _, module = self.ready(config=self.config(
                    geometry_angle_sign=sign, geometry_angle_offset_deg=4,
                    max_angle_deg=4,
                ))
                self.assertEqual(module.level().angle_deg, -4 / sign)
                self.assertEqual(module.pose.geometry_angle_deg, 0)
                self.assertTrue(module.pose.valid)

    def test_level_moves_when_inside_motion_tolerance_but_outside_level_tolerance(self):
        context, module = self.ready(config=self.config(
            angle_tolerance_deg=0.5, level_tolerance_deg=0.25,
        ))
        module.set_angle(0.3)
        self.assertEqual(module.pose.geometry_angle_deg, 0.3)
        with patch.object(module._backend, "set_angle", wraps=module._backend.set_angle) as move:
            with patch.object(module._backend, "status", wraps=module._backend.status) as status:
                result = module.level()
                move.assert_called_once()
                self.assertEqual(move.call_args.args[0], 0)
                status.assert_called_once_with()
        self.assertEqual(result.angle_deg, 0)
        self.assertEqual(module.pose.geometry_angle_deg, 0)
        self.assertTrue(module.pose.valid)
        plate = module.load_labware("memory_plate")
        self.assertIs(module.child, plate)
        self.assertEqual(len(context.loads), 1)

    def test_level_rejects_residual_accepted_by_wider_motion_tolerance(self):
        _, module = self.ready(config=self.config(
            angle_tolerance_deg=0.5, level_tolerance_deg=0.25,
        ))
        plate = module.load_labware("memory_plate")
        module.set_angle(0.3)
        residual = self.tilt.TiltStatus(0, "idle with residual angle", 0.3)
        with patch.object(module._backend, "set_angle", return_value=residual) as move:
            with patch.object(module._backend, "status", wraps=module._backend.status) as status:
                with self.assertRaises(self.tilt.TiltStateError):
                    module.level()
                move.assert_called_once()
                self.assertEqual(move.call_args.args[0], 0)
                status.assert_called_once_with()
        self.assertFalse(module.pose.valid)
        self.assertFalse(module.homed)
        self.assertIs(module.child, plate)
        self.assertTrue(plate.attached)
        with self.assertRaises(self.tilt.TiltStateError):
            plate.bottom("A1")
        self.assertTrue(module.status().is_idle)
        self.assertFalse(module.pose.valid)
        module.home()
        self.assertTrue(module.pose.valid)

    def test_failed_move_never_claims_a_new_placement_or_detaches_existing_plate(self):
        context, module = self.ready()
        labware = LabwareDouble(location="B2")
        context.fail_next_move = True
        with self.assertRaisesRegex(RuntimeError, "SDK move failure"):
            module.move_labware_onto_module(labware, use_gripper=False)
        self.assertIsNone(module.child)
        self.assertEqual(labware.location, "B2")
        self.assertFalse(module.pose.valid)
        module.home()
        plate = module.move_labware_onto_module(labware, use_gripper=False)
        context.fail_next_move = True
        with self.assertRaisesRegex(RuntimeError, "SDK move failure"):
            module.move_labware_off_module("D2", use_gripper=False)
        self.assertIs(module.child, plate)
        self.assertTrue(plate.attached)
        self.assertEqual(labware.location, "C2")
        self.assertFalse(module.pose.valid)
        with self.assertRaises(self.tilt.TiltStateError):
            plate.bottom("A1")
        self.assertEqual(len(context.moves), 3)

    def test_unload_uses_manual_off_deck_and_detaches_only_on_success(self):
        context, module = self.ready()
        plate = module.load_labware("memory_plate")
        context.fail_next_move = True
        with self.assertRaisesRegex(RuntimeError, "SDK move failure"):
            module.unload_labware()
        self.assertIs(module.child, plate)
        self.assertTrue(plate.attached)
        self.assertFalse(module.pose.valid)
        self.assertEqual(plate.labware.location, "C2")
        module.home()
        result = module.unload_labware()
        self.assertIs(result, plate.labware)
        self.assertIs(result.location, self.off_deck)
        self.assertIsNone(module.child)
        self.assertFalse(plate.attached)
        self.assertEqual(context.moves[-1], (result, self.off_deck, {"use_gripper": False}))
        with self.assertRaises(self.tilt.TiltStateError):
            plate.bottom("A1")

    def test_build_check_matches_bundle_without_importing_usb_or_sdk(self):
        script = """
import builtins
import runpy
import sys
original = builtins.__import__
def guarded(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split('.')[0] in {'usb', 'opentrons'}:
        raise AssertionError('build check tried device dependency: ' + name)
    return original(name, globals, locals, fromlist, level)
builtins.__import__ = guarded
sys.argv = [sys.argv[1], '--check']
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        result = subprocess.run(
            [sys.executable, "-c", script, str(BUILD)], cwd=self.temp.name,
            capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("matches source parts", result.stdout)


if __name__ == "__main__":
    unittest.main()

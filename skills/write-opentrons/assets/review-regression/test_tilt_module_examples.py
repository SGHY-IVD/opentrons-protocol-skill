"""Execute all four maintained tilt examples against memory-only dependencies.

The generated standalone loader and its SDK doubles come from the loader test
fixture by composition, not inheritance. No hardware, SDK simulator or physical
clearance is validated by these tests.
"""

import inspect
import math
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import test_tilt_flex_loader as loader_doubles

# Reuse the existing protocol-format memory peer without permitting real USB or
# SDK imports when this test file is executed on its own.
with patch("builtins.__import__", loader_doubles.ImportGuard()):
    import test_extension_classes as core_peers


ROOT = Path(__file__).resolve().parents[2]
SECTION = (ROOT / "references/module-practices-tilt.md").read_text().split(
    "# 第三方倾斜模块\n", 1
)[1]
BLOCKS = re.findall(r"```python\n(.*?)\n```", SECTION, flags=re.S)


class ExampleProtocol(loader_doubles.ProtocolDouble):
    def __init__(self, simulating=True, fail_move=None):
        super().__init__(simulating=simulating)
        self.comments = []
        self.fail_move = fail_move

    def comment(self, value):
        self.comments.append(value)

    def move_labware(self, labware, new_location, **kwargs):
        if len(self.moves) + 1 == self.fail_move:
            self.fail_next_move = True
        return super().move_labware(labware, new_location, **kwargs)


class TiltModuleExampleTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(len(BLOCKS), 4)
        # Composition reuses isolated single-file import and guarded SDK doubles
        # without collecting or running any loader TestCase methods a second time.
        self.fixture = loader_doubles.TiltFlexLoaderTests(methodName="runTest")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.tilt = self.fixture.tilt
        self.devices, self.peers = [], []
        self.modules, self.views, self.calls, self.backend_targets = [], [], [], []
        self.fail_tilt_motion = False

        def device_factory():
            device = core_peers.tilt.TiltDevice()
            peer = core_peers.DevicePeer()
            device.controller.transport = peer
            self.devices.append(device)
            self.peers.append(peer)
            return device

        def loader_factory(protocol, config):
            module = self.tilt.load_tilt_module(protocol, config)
            self.modules.append(module)
            set_angle = module._backend.set_angle

            def backend_set_angle(angle, speed, **kwargs):
                self.backend_targets.append(angle)
                result = set_angle(angle, speed, **kwargs)
                if self.fail_tilt_motion:
                    raise RuntimeError("synthetic failure after tilt command")
                return result

            module._backend.set_angle = backend_set_angle
            for name in (
                "connect", "disconnect", "home", "level", "load_labware",
                "set_angle", "move_labware_onto_module", "move_labware_off_module",
            ):
                actual = getattr(module, name)

                def traced(*args, _name=name, _actual=actual, **kwargs):
                    self.calls.append((_name, args, kwargs, module.child, module.labware))
                    result = _actual(*args, **kwargs)
                    if _name in {"load_labware", "move_labware_onto_module"}:
                        self.views.append(result)
                    return result

                setattr(module, name, traced)
            return module

        self.device_factory = device_factory
        self.namespace = {
            "TiltDevice": device_factory, "load_tilt_module": loader_factory,
        }
        for block in BLOCKS:
            exec(compile(block, "module-practices-tilt.md", "exec"), self.namespace)

    def config(self, **overrides):
        return self.fixture.config(**overrides)

    def call_names(self):
        return [call[0] for call in self.calls]

    def test_motion_example_uses_current_core_api_and_normal_final_angle(self):
        result = self.namespace["tilt_motion_example"](
            ExampleProtocol(simulating=False), angle_deg=8, speed_deg_s=4,
        )
        self.assertTrue(result.is_idle)
        self.assertAlmostEqual(result.angle_deg, 0)
        self.assertEqual(self.peers[0].sent.count(30001), 1)
        self.assertEqual(self.peers[0].sent.count(30002), 2)
        self.assertNotIn(30005, self.peers[0].sent)
        self.assertFalse(self.devices[0].connected)
        self.assertEqual(self.modules, [])

    def test_motion_simulation_guard_never_constructs_device_or_loader(self):
        self.namespace["TiltDevice"] = lambda: self.fail("device factory called")
        self.namespace["load_tilt_module"] = lambda *a: self.fail("loader called")
        context = ExampleProtocol(simulating=True)
        self.assertIsNone(self.namespace["tilt_motion_example"](context, angle_deg=8))
        self.assertEqual(len(context.comments), 1)
        self.assertEqual(self.devices, [])
        self.assertEqual(self.modules, [])

    def test_core_motion_failure_closes_without_automatic_return_motion(self):
        original_factory = self.device_factory

        def failing_factory():
            device = original_factory()
            peer = self.peers[-1]
            original_write = peer.write

            def write(request):
                count = original_write(request)
                if peer.sent[-1] == 30002:
                    raise RuntimeError("synthetic failure after motion request")
                return count

            peer.write = write
            return device

        self.namespace["TiltDevice"] = failing_factory
        with self.assertRaisesRegex(RuntimeError, "after motion request"):
            self.namespace["tilt_motion_example"](
                ExampleProtocol(simulating=False), angle_deg=8,
            )
        self.assertEqual(self.peers[0].sent.count(30002), 1)
        self.assertFalse(self.devices[0].connected)

    def test_record_example_binds_plate_runs_tilt_levels_and_returns_native_labware(self):
        context = ExampleProtocol()
        returned = self.namespace["tilt_plate_record_example"](
            context, config=self.config(), load_name="example_plate", angle_deg=8,
        )
        module, view = self.modules[0], self.views[0]
        self.assertIs(returned, context.loads[0])
        self.assertIs(returned, view.labware)
        self.assertIs(module.child, view)
        self.assertIs(module.labware, returned)
        self.assertEqual((returned.load_name, returned.location, returned.label),
                         ("example_plate", "C2", "倾斜板"))
        self.assertEqual(self.call_names(), [
            "connect", "home", "level", "load_labware", "set_angle",
            "level", "set_angle", "disconnect",
        ])
        for name, _, _, child, labware in self.calls:
            if name == "set_angle":
                self.assertIs(child, view)
                self.assertIs(labware, returned)
        self.assertEqual(self.backend_targets, [8, 0])
        self.assertEqual(module.angle, 0)
        self.assertFalse(module.connected)
        self.assertFalse(module.pose.valid)
        self.assertTrue(view.attached)
        self.assertEqual(context.moves, [])
        self.assertEqual(self.devices, [])
        with self.assertRaises(self.tilt.TiltStateError):
            view.bottom("A1")

    def test_record_example_tilt_failure_preserves_plate_and_does_not_level_again(self):
        self.fail_tilt_motion = True
        context = ExampleProtocol()
        with self.assertRaisesRegex(RuntimeError, "after tilt command"):
            self.namespace["tilt_plate_record_example"](
                context, config=self.config(), load_name="example_plate", angle_deg=8,
            )
        module, view = self.modules[0], self.views[0]
        self.assertEqual(self.backend_targets, [8])
        self.assertEqual(self.call_names(), [
            "connect", "home", "level", "load_labware", "set_angle", "disconnect",
        ])
        self.assertIs(module.child, view)
        self.assertIs(module.labware, context.loads[0])
        self.assertEqual(context.loads[0].location, "C2")
        self.assertEqual(context.moves, [])
        self.assertFalse(module.connected)
        self.assertFalse(module.pose.valid)

    def test_record_example_sdk_load_failure_does_not_claim_a_loaded_plate(self):
        context = ExampleProtocol()
        with patch.object(context, "load_labware", side_effect=RuntimeError("SDK load failed")):
            with self.assertRaisesRegex(RuntimeError, "SDK load failed"):
                self.namespace["tilt_plate_record_example"](
                    context, config=self.config(), load_name="example_plate", angle_deg=8,
                )
        module = self.modules[0]
        self.assertIsNone(module.child)
        self.assertIsNone(module.labware)
        self.assertEqual(self.views, [])
        self.assertEqual(self.backend_targets, [])
        self.assertEqual(context.moves, [])
        self.assertEqual(self.call_names()[-1], "disconnect")
        self.assertFalse(module.connected)

    def test_move_example_binds_tilts_levels_and_uses_correct_gripper_offset_legs(self):
        context = ExampleProtocol()
        labware = loader_doubles.LabwareDouble(location="B2")
        returned = self.namespace["tilt_plate_move_example"](
            context, labware, config=self.config(
                gripper_drop_x_mm=1, gripper_drop_y_mm=2, gripper_drop_z_mm=13,
                gripper_pick_up_x_mm=4, gripper_pick_up_y_mm=5, gripper_pick_up_z_mm=17,
            ), end_slot="D2", angle_deg=8,
        )
        module, view = self.modules[0], self.views[0]
        self.assertIs(returned, labware)
        self.assertEqual(returned.location, "D2")
        self.assertEqual(context.moves, [
            (labware, "C2", {
                "use_gripper": True, "pick_up_offset": None,
                "drop_offset": {"x": 1, "y": 2, "z": 13},
            }),
            (labware, "D2", {
                "use_gripper": True, "pick_up_offset": {"x": 4, "y": 5, "z": 17},
                "drop_offset": None,
            }),
        ])
        self.assertEqual(self.call_names(), [
            "connect", "home", "level", "move_labware_onto_module", "set_angle",
            "level", "set_angle", "move_labware_off_module", "disconnect",
        ])
        for name, _, _, child, recorded_labware in self.calls:
            if name == "set_angle":
                self.assertIs(child, view)
                self.assertIs(recorded_labware, labware)
        self.assertEqual(self.backend_targets, [8, 0])
        self.assertEqual(module.angle, 0)
        self.assertIsNone(module.child)
        self.assertIsNone(module.labware)
        self.assertFalse(view.attached)
        self.assertFalse(module.connected)
        self.assertFalse(module.pose.valid)
        self.assertEqual(context.loads, [])
        self.assertEqual(self.devices, [])

    def test_move_example_tilt_failure_does_not_level_or_move_plate_off(self):
        self.fail_tilt_motion = True
        context = ExampleProtocol()
        labware = loader_doubles.LabwareDouble(location="B2")
        with self.assertRaisesRegex(RuntimeError, "after tilt command"):
            self.namespace["tilt_plate_move_example"](
                context, labware, config=self.config(
                    gripper_drop_z_mm=13, gripper_pick_up_z_mm=17,
                ), end_slot="D2", angle_deg=8,
            )
        module, view = self.modules[0], self.views[0]
        self.assertEqual(labware.location, "C2")
        self.assertIs(module.child, view)
        self.assertIs(module.labware, labware)
        self.assertTrue(view.attached)
        self.assertEqual(len(context.moves), 1)
        self.assertEqual(self.backend_targets, [8])
        self.assertEqual(self.call_names(), [
            "connect", "home", "level", "move_labware_onto_module", "set_angle", "disconnect",
        ])
        self.assertFalse(module.connected)
        self.assertFalse(module.pose.valid)

    def test_move_example_sdk_failure_never_claims_final_placement_or_retries(self):
        for fail_move in (1, 2):
            with self.subTest(fail_move=fail_move):
                self.modules.clear()
                self.views.clear()
                self.calls.clear()
                self.backend_targets.clear()
                context = ExampleProtocol(fail_move=fail_move)
                labware = loader_doubles.LabwareDouble(location="B2")
                with self.assertRaisesRegex(RuntimeError, "SDK move failure"):
                    self.namespace["tilt_plate_move_example"](
                        context, labware, config=self.config(
                            gripper_drop_z_mm=13, gripper_pick_up_z_mm=17,
                        ), end_slot="D2", angle_deg=8,
                    )
                module = self.modules[0]
                self.assertEqual(len(context.moves), fail_move)
                self.assertEqual(labware.location, "B2" if fail_move == 1 else "C2")
                self.assertEqual(self.backend_targets, [] if fail_move == 1 else [8, 0])
                self.assertEqual(self.call_names()[-1], "disconnect")
                self.assertFalse(module.connected)
                self.assertFalse(module.pose.valid)
                if fail_move == 1:
                    self.assertIsNone(module.child)
                    self.assertIsNone(module.labware)
                else:
                    self.assertIs(module.child, self.views[0])
                    self.assertIs(module.labware, labware)
                    self.assertTrue(self.views[0].attached)

    def test_locations_example_computes_all_three_locations_without_double_translation(self):
        context, module = self.fixture.ready()
        view = module.load_labware("example_plate")
        module.set_angle(30)
        locations = self.namespace["tilt_plate_locations_example"](
            view, well_name="A1", local_z=1,
        )
        self.assertEqual(set(locations), {"bottom", "center", "top"})
        expected = {
            "bottom": loader_doubles.Point(63 - 25 * math.sqrt(3), 20, 43 + 3 * math.sqrt(3)),
            "center": loader_doubles.Point(65 - 25 * math.sqrt(3), 20, 43 + 5 * math.sqrt(3)),
            "top": loader_doubles.Point(67.5 - 25 * math.sqrt(3), 20, 43 + 7.5 * math.sqrt(3)),
        }
        for name, location in locations.items():
            self.fixture.assertPointAlmostEqual(location.point, expected[name])
            self.assertIs(location.labware, view.labware.wells_by_name()["A1"])
        self.assertEqual(module.angle, 30)
        self.assertEqual(context.moves, [])
        module.disconnect()

    def test_locations_example_rejects_invalid_pose_after_disconnect(self):
        _, module = self.fixture.ready()
        view = module.load_labware("example_plate")
        module.disconnect()
        self.assertTrue(view.attached)
        with self.assertRaises(self.tilt.TiltStateError):
            self.namespace["tilt_plate_locations_example"](view, well_name="A1", local_z=1)

    def test_locations_example_rejects_detached_old_plate_even_with_valid_module_pose(self):
        _, module = self.fixture.ready()
        view = module.load_labware("example_plate")
        module.move_labware_off_module("D2", use_gripper=False)
        module.load_labware("replacement")
        self.assertTrue(module.pose.valid)
        self.assertFalse(view.attached)
        with self.assertRaises(self.tilt.TiltStateError):
            self.namespace["tilt_plate_locations_example"](view, well_name="A1", local_z=1)
        module.disconnect()

    def test_documented_constructor_matches_current_parameter_contract(self):
        text = (ROOT / "references/api-module-tilt.md").read_text()
        signature_text = re.search(r"```text\n(TiltDevice\(.*?\))\n```", text, re.S)[1]
        namespace = {}
        exec("def documented" + signature_text[len("TiltDevice"):] + ":\n    pass\n", namespace)

        def parameters(callable):
            return [(p.name, p.kind, p.default)
                    for p in inspect.signature(callable).parameters.values()]

        self.assertEqual(parameters(namespace["documented"]), parameters(self.tilt.TiltDevice))


if __name__ == "__main__":
    unittest.main()

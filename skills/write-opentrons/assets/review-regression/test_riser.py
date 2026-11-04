"""Memory-only regression tests of the standalone ordinary-deck Riser helper.

Only riser.py is copied into an isolated directory. Real SDK and USB imports
are rejected. The peers preserve native object identity and occupied locations;
they do not validate robot motion, labware compatibility or physical clearance.
"""

import builtins
import importlib.util
import math
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "assets/python/helpers/riser.py"
REFERENCE = ROOT / "references/api-riser.md"
GENERIC_PLATE = "generic_stack_arithmetic_plate"


class ImportGuard:
    """A copied standalone helper must not load robot or USB dependencies."""

    def __init__(self):
        self.original = builtins.__import__
        self.attempts = []

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] in {"opentrons", "usb", "serial"}:
            self.attempts.append(name)
            raise AssertionError("unexpected robot/USB dependency: " + name)
        if level:
            raise AssertionError("standalone helper used a relative import")
        return self.original(name, globals, locals, fromlist, level)


class NativeLabwarePeer:
    """A protocol-owned Labware, never a helper-created proxy or wrapper."""

    def __init__(self, load_name, parent, label):
        self.load_name = load_name
        self.parent = parent
        self.label = label


class ModuleDestinationPeer:
    """An opaque SDK-style destination object, distinct from its deck slot."""

    def __init__(self, slot="D1"):
        self.slot = slot


class MemoryProtocol:
    """Enforce one registered native object at a location, with failure hooks."""

    def __init__(self):
        self.events = []
        self.load_calls = []
        self.loaded = []
        self.moves = []
        self.comments = []
        self.occupants = {}
        self.fail_load_number = None
        self.move_failure = None
        self.load_error = RuntimeError("synthetic native load failure")
        self.move_error = RuntimeError("synthetic native move failure")

    def load_labware(self, load_name, location, label=None):
        self.events.append(("load", load_name, location, label))
        self.load_calls.append((load_name, location, label))
        if len(self.load_calls) == self.fail_load_number:
            raise self.load_error
        if location in self.occupants:
            raise AssertionError("helper registered overlapping virtual plates")
        native = NativeLabwarePeer(load_name, location, label)
        self.loaded.append(native)
        self.occupants[location] = native
        return native

    def comment(self, value):
        self.events.append(("comment", value))
        self.comments.append(value)

    def move_labware(self, labware, new_location, **kwargs):
        self.events.append(("move", labware, new_location, kwargs))
        self.moves.append((labware, new_location, kwargs))
        if self.move_failure == "before":
            raise self.move_error
        if self.occupants.get(labware.parent) is not labware:
            raise AssertionError("move did not receive the registered native top")
        if new_location in self.occupants:
            raise AssertionError("destination already occupied")
        del self.occupants[labware.parent]
        labware.parent = new_location
        self.occupants[new_location] = labware
        if self.move_failure == "after":
            raise self.move_error


class RiserFixture(unittest.TestCase):
    """Reusable fixture without inherited test methods or SDK installation."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="standalone-riser-test-")
        self.addCleanup(self.temp.cleanup)
        isolated = Path(self.temp.name) / "riser.py"
        shutil.copyfile(TARGET, isolated)
        self.assertEqual([p.name for p in isolated.parent.iterdir()], ["riser.py"])
        module_name = "_isolated_riser_regression"
        spec = importlib.util.spec_from_file_location(module_name, isolated)
        self.helper = importlib.util.module_from_spec(spec)
        module_patch = patch.dict(sys.modules, {module_name: self.helper})
        module_patch.start()
        self.addCleanup(module_patch.stop)
        self.guard = ImportGuard()
        guarded_import = patch("builtins.__import__", self.guard)
        guarded_import.start()
        self.addCleanup(guarded_import.stop)
        spec.loader.exec_module(self.helper)
        self.assertEqual(self.guard.attempts, [])
        self.assertEqual(self.helper.__package__, "")
        self.context = MemoryProtocol()

    def riser(self, **overrides):
        options = dict(
            protocol=self.context, slot_name="C4", load_name=GENERIC_PLATE,
            quantity=5, stack_height_mm=13, riser_base_height_mm=2,
        )
        options.update(overrides)
        return self.helper.Riser(**options)

    def assertBlockedWithoutEffects(self, riser, destination="B1"):
        before = list(self.context.events)
        with self.assertRaises(self.helper.RiserStateError):
            riser.move_next_to(destination)
        self.assertEqual(self.context.events, before)


class RiserTests(RiserFixture):
    def test_five_layer_arithmetic_and_native_identity_across_all_moves(self):
        # Five layers and 13 mm are arithmetic fixtures, not physical PCR claims.
        riser = self.riser()
        first = riser.current_labware
        self.assertIs(first, self.context.loaded[0])
        self.assertEqual(self.context.occupants, {"C4": first})
        self.assertEqual(len(self.context.load_calls), 1)
        self.assertIsNone(riser.last_moved_labware)
        destinations = ["C2", "D2", "B2", "A2", "A3"]
        moved = []
        for remaining, destination in zip((4, 3, 2, 1, 0), destinations):
            captured = riser.current_labware
            returned = riser.move_next_to(destination)
            moved.append(returned)
            self.assertIs(returned, captured)
            self.assertIs(returned, self.context.moves[-1][0])
            self.assertEqual(returned.parent, destination)
            self.assertEqual(riser.quantity, remaining)
            self.assertIs(riser.last_moved_labware, returned)
            self.assertFalse(riser.faulted)
            if remaining:
                self.assertIs(riser.current_labware, self.context.loaded[-1])
                self.assertIsNot(riser.current_labware, returned)
                self.assertEqual(riser.current_labware.parent, "C4")
                self.assertIs(self.context.occupants["C4"], riser.current_labware)
            else:
                self.assertIsNone(riser.current_labware)
                self.assertNotIn("C4", self.context.occupants)
        self.assertEqual([m[2]["pick_up_offset"]["z"] for m in self.context.moves],
                         [54, 41, 28, 15, 2])
        self.assertEqual(len({id(native) for native in moved}), 5)
        self.assertEqual(len(self.context.load_calls), 5)
        for native, destination in zip(moved, destinations):
            self.assertEqual(native.parent, destination)
        for _, _, kwargs in self.context.moves:
            self.assertIs(kwargs["use_gripper"], True)
            self.assertEqual(set(kwargs), {"use_gripper", "pick_up_offset", "drop_offset"})
            self.assertEqual(kwargs["pick_up_offset"]["x"], 0)
            self.assertEqual(kwargs["pick_up_offset"]["y"], 0)
            self.assertEqual(kwargs["drop_offset"], {"x": 0, "y": 0, "z": 0})
        self.assertBlockedWithoutEffects(riser)

    def test_one_layer_uses_base_without_reloading(self):
        riser = self.riser(quantity=1, riser_base_height_mm=4.5)
        native = riser.current_labware
        self.assertIs(riser.move_next_to("C2"), native)
        self.assertEqual(self.context.moves[0][2]["pick_up_offset"],
                         {"x": 0, "y": 0, "z": 4.5})
        self.assertEqual(len(self.context.load_calls), 1)
        self.assertEqual(riser.quantity, 0)
        self.assertIsNone(riser.current_labware)
        self.assertBlockedWithoutEffects(riser)

    def test_zero_quantity_registers_no_labware_and_stays_empty(self):
        riser = self.riser(quantity=0)
        self.assertEqual(self.context.events, [])
        self.assertEqual(riser.quantity, 0)
        self.assertIsNone(riser.current_labware)
        self.assertIsNone(riser.last_moved_labware)
        self.assertFalse(riser.faulted)
        self.assertBlockedWithoutEffects(riser)
        self.assertFalse(riser.faulted)

    def test_valid_large_quantity_has_no_fixed_layer_limit_or_eager_loading(self):
        riser = self.riser(quantity=5000, stack_height_mm=0.001,
                           riser_base_height_mm=0)
        self.assertEqual(riser.quantity, 5000)
        self.assertEqual(len(self.context.loaded), 1)
        self.assertEqual(len(self.context.occupants), 1)
        riser.move_next_to("C2")
        self.assertAlmostEqual(self.context.moves[0][2]["pick_up_offset"]["z"], 4.999)
        self.assertEqual(riser.quantity, 4999)
        self.assertEqual(len(self.context.loaded), 2)

    def test_quantity_must_be_nonnegative_integer_excluding_bool_before_load(self):
        for value in (-1, 1.5, 2.0, True, False, "2", None, math.nan, math.inf):
            with self.subTest(quantity=value):
                with self.assertRaises(ValueError):
                    self.riser(quantity=value)
                self.assertEqual(self.context.events, [])

    def test_pitch_and_base_reject_invalid_values_before_load_even_when_empty(self):
        invalid = {
            "stack_height_mm": (0, -1, math.nan, math.inf, -math.inf, True, "13", None),
            "riser_base_height_mm": (-1, math.nan, math.inf, -math.inf, True, "2", None),
        }
        for name, values in invalid.items():
            for value in values:
                for quantity in (0, 1, 5):
                    with self.subTest(parameter=name, value=value, quantity=quantity):
                        with self.assertRaises(ValueError):
                            self.riser(quantity=quantity, **{name: value})
                        self.assertEqual(self.context.events, [])

    def test_top_height_overflow_is_rejected_before_initial_load(self):
        for options in (
            dict(quantity=10 ** 309, stack_height_mm=1),
            dict(quantity=3, stack_height_mm=1e308),
            dict(quantity=2, stack_height_mm=1e308, riser_base_height_mm=1e308),
        ):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    self.riser(**options)
                self.assertEqual(self.context.events, [])

    def test_invalid_origin_or_load_name_is_rejected_before_loading(self):
        for name in ("slot_name", "load_name"):
            for value in ("", "  ", None, 4):
                with self.subTest(parameter=name, value=value):
                    with self.assertRaises(ValueError):
                        self.riser(**{name: value})
                    self.assertEqual(self.context.events, [])

    def test_same_source_target_is_rejected_before_any_effect(self):
        riser = self.riser()
        native = riser.current_labware
        for target in ("C4", "c4", " c4 "):
            with self.subTest(target=target):
                before = list(self.context.events)
                with self.assertRaises(ValueError):
                    riser.move_next_to(target)
                self.assertEqual(self.context.events, before)
                self.assertIs(riser.current_labware, native)
                self.assertEqual(riser.quantity, 5)
                self.assertFalse(riser.faulted)

    def test_module_destination_is_passed_as_the_original_sdk_object(self):
        riser = self.riser(quantity=1)
        target = ModuleDestinationPeer()
        native = riser.move_next_to(target)
        self.assertIs(self.context.moves[0][1], target)
        self.assertIs(native.parent, target)
        self.assertIs(self.context.occupants[target], native)

    def test_drop_offset_uses_finite_xyz_and_zero_for_missing_axes(self):
        riser = self.riser(quantity=2)
        supplied = MappingProxyType({"x": -1.5, "z": 0.75})
        riser.move_next_to("C2", drop_offset=supplied)
        self.assertEqual(self.context.moves[0][2]["drop_offset"],
                         {"x": -1.5, "y": 0, "z": 0.75})
        self.assertEqual(dict(supplied), {"x": -1.5, "z": 0.75})
        self.assertEqual(self.context.moves[0][2]["pick_up_offset"]["z"], 15)
        riser.move_next_to("D2", drop_offset={})
        self.assertEqual(self.context.moves[1][2]["drop_offset"],
                         {"x": 0, "y": 0, "z": 0})

    def test_invalid_drop_offset_rejects_before_comment_or_motion(self):
        riser = self.riser()
        invalid = [[], "xyz", {"q": 1}, {"x": True}, {"y": "1"},
                   {"z": None}, {"x": math.nan}, {"y": math.inf}, {"z": -math.inf}]
        for offset in invalid:
            with self.subTest(offset=offset):
                before = list(self.context.events)
                with self.assertRaises(ValueError):
                    riser.move_next_to("C2", drop_offset=offset)
                self.assertEqual(self.context.events, before)
                self.assertEqual(riser.quantity, 5)
                self.assertFalse(riser.faulted)
        before = list(self.context.events)
        with self.assertRaises(TypeError):
            riser.move_next_to("C2", {"z": 1})
        self.assertEqual(self.context.events, before)

    def test_move_exception_preserves_records_and_blocks_blind_retry(self):
        for failure_stage in ("before", "after"):
            with self.subTest(failure_stage=failure_stage):
                self.context = MemoryProtocol()
                riser = self.riser(quantity=3)
                previous = riser.move_next_to("C2")
                captured = riser.current_labware
                self.context.move_failure = failure_stage
                with self.assertRaises(RuntimeError) as error:
                    riser.move_next_to("D2")
                self.assertIs(error.exception, self.context.move_error)
                self.assertEqual(riser.quantity, 2)
                self.assertIs(riser.current_labware, captured)
                self.assertIs(riser.last_moved_labware, previous)
                self.assertTrue(riser.faulted)
                self.assertEqual(len(self.context.load_calls), 2)
                self.assertEqual(len(self.context.moves), 2)
                self.assertEqual(captured.parent,
                                 "C4" if failure_stage == "before" else "D2")
                self.assertBlockedWithoutEffects(riser)

    def test_successful_move_then_reload_failure_keeps_consumed_inventory(self):
        riser = self.riser(quantity=3)
        moved = riser.current_labware
        self.context.fail_load_number = 2
        with self.assertRaises(RuntimeError) as error:
            riser.move_next_to("C2")
        self.assertIs(error.exception, self.context.load_error)
        self.assertEqual(riser.quantity, 2)
        self.assertIsNone(riser.current_labware)
        self.assertIs(riser.last_moved_labware, moved)
        self.assertEqual(moved.parent, "C2")
        self.assertNotIn("C4", self.context.occupants)
        self.assertTrue(riser.faulted)
        self.assertEqual(len(self.context.moves), 1)
        self.assertEqual(len(self.context.load_calls), 2)
        self.assertBlockedWithoutEffects(riser)

    def test_initial_load_failure_propagates_without_retry_or_movement(self):
        self.context.fail_load_number = 1
        with self.assertRaises(RuntimeError) as error:
            self.riser()
        self.assertIs(error.exception, self.context.load_error)
        self.assertEqual(len(self.context.load_calls), 1)
        self.assertEqual(self.context.moves, [])
        self.assertEqual(self.context.comments, [])

    def test_interrupt_during_move_or_reload_propagates_and_blocks_continuation(self):
        for boundary in ("move", "reload"):
            with self.subTest(boundary=boundary):
                self.context = MemoryProtocol()
                riser = self.riser(quantity=2)
                native = riser.current_labware
                interruption = KeyboardInterrupt("synthetic operator interruption")
                if boundary == "move":
                    self.context.move_failure = "after"
                    self.context.move_error = interruption
                else:
                    self.context.fail_load_number = 2
                    self.context.load_error = interruption
                with self.assertRaises(KeyboardInterrupt) as error:
                    riser.move_next_to("C2")
                self.assertIs(error.exception, interruption)
                self.assertTrue(riser.faulted)
                self.assertEqual(native.parent, "C2")
                if boundary == "move":
                    self.assertEqual(riser.quantity, 2)
                    self.assertIs(riser.current_labware, native)
                    self.assertIsNone(riser.last_moved_labware)
                    self.assertEqual(len(self.context.load_calls), 1)
                else:
                    self.assertEqual(riser.quantity, 1)
                    self.assertIsNone(riser.current_labware)
                    self.assertIs(riser.last_moved_labware, native)
                    self.assertEqual(len(self.context.load_calls), 2)
                self.assertBlockedWithoutEffects(riser)

    def test_bookkeeping_properties_are_read_only(self):
        riser = self.riser()
        for name in ("quantity", "current_labware", "last_moved_labware", "faulted"):
            with self.subTest(property=name):
                with self.assertRaises(AttributeError):
                    setattr(riser, name, None)

    def test_operator_comments_and_generic_labels_do_not_claim_stacker_or_pcr(self):
        riser = self.riser(quantity=1)
        riser.move_next_to("C2")
        self.assertTrue(self.context.comments)
        for text in self.context.comments:
            self.assertIsInstance(text, str)
            self.assertNotRegex(text, r"(?i)stacker|\bz\b|z[-_ ]?offset")
        for native in self.context.loaded:
            self.assertIsInstance(native.label, str)
            self.assertNotRegex(native.label, r"(?i)stacker|pcr")
        self.assertEqual(self.guard.attempts, [])


class RiserReferenceExampleTests(RiserFixture):
    def test_two_maintained_examples_execute_against_the_standalone_api(self):
        blocks = re.findall(r"```python\n(.*?)\n```", REFERENCE.read_text(), re.S)
        self.assertEqual(len(blocks), 2)
        namespace = {"Riser": self.helper.Riser}
        for block in blocks:
            exec(compile(block, "api-riser.md", "exec"), namespace)

        riser, first, second = namespace["riser_supply_example"](
            self.context, stack_height_mm=7.5, riser_base_height_mm=1,
        )
        self.assertEqual((first.parent, second.parent), ("C2", "D2"))
        self.assertIs(first, self.context.loaded[0])
        self.assertIs(second, self.context.loaded[1])
        self.assertEqual(riser.quantity, 2)
        self.assertEqual([m[2]["pick_up_offset"]["z"] for m in self.context.moves],
                         [23.5, 16])
        self.assertEqual(first.load_name,
                         "opentrons_96_wellplate_200ul_pcr_full_skirt")

        target = ModuleDestinationPeer()
        other = MemoryProtocol()
        custom, moved = namespace["riser_custom_target_example"](
            other, source_slot="B3", load_name=GENERIC_PLATE, quantity=2,
            stack_height_mm=8, riser_base_height_mm=3,
            target_location=target, drop_offset={"x": 0.2, "z": -0.5},
        )
        self.assertIs(moved, other.loaded[0])
        self.assertIs(moved.parent, target)
        self.assertIs(other.moves[0][1], target)
        self.assertEqual(other.moves[0][2]["pick_up_offset"],
                         {"x": 0, "y": 0, "z": 11})
        self.assertEqual(other.moves[0][2]["drop_offset"],
                         {"x": 0.2, "y": 0, "z": -0.5})
        self.assertEqual(custom.quantity, 1)
        self.assertIs(custom.current_labware, other.loaded[1])
        self.assertEqual(custom.current_labware.parent, "B3")
        self.assertEqual(self.guard.attempts, [])


if __name__ == "__main__":
    unittest.main()

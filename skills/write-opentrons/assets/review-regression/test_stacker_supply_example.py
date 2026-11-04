"""Execute the maintained Flex Stacker supply example with memory-only peers.

The official-style ledger, native object identities and partial command effects
are represented in memory. No installed Opentrons SDK, USB, robot connection,
motion, lid compatibility or physical clearance is validated by these tests.
"""

import builtins
import re
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "references/module-practices.md"
OFF_DECK = object()


class Cancelled(BaseException):
    """An interrupted command must not trigger another supply operation."""


class NativeLabwarePeer:
    def __init__(self, label, load_name, lid_name):
        self.label, self.load_name = label, load_name
        self.parent = OFF_DECK
        self.lid_name = lid_name
        self.lid_location = self


class FailureHooks:
    def __init__(self, phase=None, timing=None, error=None):
        self.phase, self.timing, self.error = phase, timing, error

    def check(self, phase, number, timing):
        if (phase, number, timing) == (self.phase, 2, self.timing):
            raise self.error


class MemoryStacker:
    """A native inventory ledger distinct from the shuttle's current object."""

    def __init__(self, events, failures):
        self.events, self.failures = events, failures
        self.labware = None
        self.inventory = []
        self.initial_objects = []
        self.configurations, self.returned_objects = [], []
        self.retrieve_calls = 0
        self.shuttle_on_retrieve = []

    def set_stored_labware(self, *, load_name, count, lid):
        self.events.append(("set_stored_labware", load_name, count, lid))
        if self.configurations or self.inventory or self.labware is not None:
            raise AssertionError("the caller must declare initial inventory only once")
        self.configurations.append((load_name, count, lid))
        self.inventory = [NativeLabwarePeer(str(index), load_name, lid)
                          for index in range(count)]
        self.initial_objects = list(self.inventory)

    def get_stored_labware(self):
        return list(self.inventory)

    def retrieve(self):
        self.retrieve_calls += 1
        self.events.append(("retrieve", self.retrieve_calls))
        self.shuttle_on_retrieve.append(self.labware)
        self.failures.check("retrieve", self.retrieve_calls, "before")
        if self.labware is not None or not self.inventory:
            raise AssertionError("retrieve requires stock and an empty shuttle")
        native = self.inventory.pop(0)
        native.parent = self
        self.labware = native
        self.failures.check("retrieve", self.retrieve_calls, "after")
        self.returned_objects.append(native)
        return native


class MemoryProtocol:
    def __init__(self, failures):
        self.events, self.failures = [], failures
        self.stacker = MemoryStacker(self.events, failures)
        self.chute = object()
        self.module_loads, self.chute_loads = [], 0
        self.moves, self.lid_moves, self.occupants = [], [], {}

    def load_module(self, model, location):
        self.events.append(("load_module", model, location))
        self.module_loads.append((model, location))
        if len(self.module_loads) != 1:
            raise AssertionError("the example must reuse its loaded native Stacker")
        return self.stacker

    def load_waste_chute(self):
        self.events.append(("load_waste_chute",))
        self.chute_loads += 1
        if self.chute_loads != 1:
            raise AssertionError("the example loaded an extra waste chute")
        return self.chute

    def move_labware(self, labware, *, new_location, use_gripper):
        number = len(self.moves) + 1
        self.events.append(("move_labware", number, labware, new_location))
        self.moves.append((labware, new_location, use_gripper))
        self.failures.check("move_labware", number, "before")
        if self.stacker.labware is not labware or labware.parent is not self.stacker:
            raise AssertionError("move must receive the native retrieved shuttle object")
        if use_gripper is not True or new_location in self.occupants:
            raise AssertionError("the example needs the gripper and an empty destination")
        self.stacker.labware = None
        labware.parent = new_location
        self.occupants[new_location] = labware
        self.failures.check("move_labware", number, "after")

    def move_lid(self, source_location, *, new_location, use_gripper):
        number = len(self.lid_moves) + 1
        self.events.append(("move_lid", number, source_location, new_location))
        self.lid_moves.append((source_location, new_location, use_gripper))
        self.failures.check("move_lid", number, "before")
        if self.occupants.get(source_location.parent) is not source_location:
            raise AssertionError("move_lid must follow positioning the same native object")
        if (source_location.lid_location is not source_location
                or use_gripper is not True or new_location is not self.chute):
            raise AssertionError("move_lid must use the covered rack and loaded chute")
        source_location.lid_location = new_location
        self.failures.check("move_lid", number, "after")


class StackerSupplyExampleTests(unittest.TestCase):
    def setUp(self):
        source = REFERENCE.read_text(encoding="utf-8")
        section = re.search(
            r"^### 连续供料与对象引用\n(.*?)(?=^#{2,3} |\Z)", source, re.M | re.S)
        self.assertIsNotNone(section, "the maintained supply section must exist")
        blocks = re.findall(r"```python\n(.*?)```", section.group(1), re.S)
        self.assertEqual(len(blocks), 1, "execute the section's sole Python example")
        self.code = compile(blocks[0], str(REFERENCE), "exec")

    def execute(self, phase=None, timing=None, error=None):
        self.protocol = MemoryProtocol(FailureHooks(phase, timing, error))
        self.namespace = {"protocol": self.protocol}
        original_import = builtins.__import__

        def offline_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.split(".", 1)[0] in {"opentrons", "usb", "serial"}:
                raise AssertionError("unexpected SDK or hardware import: " + name)
            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", offline_import):
            exec(self.code, self.namespace)

    def assertFailureState(self, phase, timing, error):
        with self.assertRaises(type(error)) as raised:
            self.execute(phase, timing, error)
        self.assertIs(raised.exception, error)
        protocol, stacker = self.protocol, self.protocol.stacker
        first, second, third = stacker.initial_objects
        references = self.namespace["retrieved_labware"]
        self.assertEqual(references, stacker.returned_objects)
        self.assertEqual(protocol.events[-1][0], phase)
        self.assertEqual(stacker.retrieve_calls, 2)
        self.assertEqual(stacker.shuttle_on_retrieve, [None, None])
        self.assertEqual(stacker.configurations,
                         [("opentrons_flex_96_tiprack_50ul", 3,
                           "opentrons_flex_tiprack_lid")])
        self.assertIs(self.namespace["stacker"], stacker)
        self.assertEqual(first.parent, "B2")
        self.assertIs(first.lid_location, protocol.chute)
        self.assertIs(third.parent, OFF_DECK)

        if phase == "retrieve":
            # A call that raised did not return an object for append(), even
            # when its native ledger/location changed before the interruption.
            self.assertEqual(references, [first])
            self.assertEqual(len(protocol.moves), 1)
            self.assertEqual(len(protocol.lid_moves), 1)
            if timing == "before":
                self.assertEqual(stacker.get_stored_labware(), [second, third])
                self.assertIsNone(stacker.labware)
                self.assertIs(second.parent, OFF_DECK)
            else:
                self.assertEqual(stacker.get_stored_labware(), [third])
                self.assertIs(stacker.labware, second)
                self.assertIs(second.parent, stacker)
        else:
            self.assertEqual(references, [first, second])
            self.assertEqual(stacker.get_stored_labware(), [third])
            self.assertEqual(len(protocol.moves), 2)
            self.assertEqual(len(protocol.lid_moves), 1 if phase == "move_labware" else 2)
            if phase == "move_labware" and timing == "before":
                self.assertIs(stacker.labware, second)
                self.assertIs(second.parent, stacker)
            else:
                self.assertIsNone(stacker.labware)
                self.assertEqual(second.parent, "C2")
            self.assertIs(second.lid_location,
                          protocol.chute if phase == "move_lid" and timing == "after"
                          else second)

    def test_three_native_objects_are_retained_positioned_and_delidded_in_order(self):
        self.execute()
        protocol, stacker = self.protocol, self.protocol.stacker
        native = stacker.initial_objects
        self.assertEqual(protocol.module_loads, [("flexStackerModuleV1", "A4")])
        self.assertEqual(protocol.chute_loads, 1)
        self.assertEqual(stacker.configurations,
                         [("opentrons_flex_96_tiprack_50ul", 3,
                           "opentrons_flex_tiprack_lid")])
        references = self.namespace["retrieved_labware"]
        self.assertEqual(len(references), 3)
        for index, destination in enumerate(("B2", "C2", "D2")):
            self.assertIs(references[index], native[index])
            self.assertIs(stacker.returned_objects[index], native[index])
            self.assertIs(protocol.moves[index][0], native[index])
            self.assertEqual(protocol.moves[index][1:], (destination, True))
            self.assertEqual(native[index].parent, destination)
            self.assertIs(protocol.occupants[destination], native[index])
            self.assertIs(protocol.lid_moves[index][0], native[index])
            self.assertIs(protocol.lid_moves[index][1], protocol.chute)
            self.assertIs(protocol.lid_moves[index][2], True)
            self.assertIs(native[index].lid_location, protocol.chute)
        self.assertEqual(stacker.retrieve_calls, 3)
        self.assertEqual(stacker.shuttle_on_retrieve, [None, None, None])
        self.assertEqual(stacker.get_stored_labware(), [])
        self.assertIsNone(stacker.labware)
        self.assertEqual([event[0] for event in protocol.events],
                         ["load_module", "set_stored_labware", "load_waste_chute"]
                         + ["retrieve", "move_labware", "move_lid"] * 3)

    def test_retrieve_failure_preserves_native_inventory_and_returned_references(self):
        for timing in ("before", "after"):
            with self.subTest(timing=timing):
                self.assertFailureState("retrieve", timing, RuntimeError("retrieve failed"))

    def test_move_failure_keeps_successful_retrieval_reference_without_another_item(self):
        for timing in ("before", "after"):
            with self.subTest(timing=timing):
                self.assertFailureState("move_labware", timing, RuntimeError("move failed"))

    def test_lid_failure_keeps_positioned_object_without_rollback_or_next_retrieve(self):
        for timing in ("before", "after"):
            with self.subTest(timing=timing):
                self.assertFailureState("move_lid", timing, RuntimeError("lid failed"))

    def test_cancellation_propagates_at_each_phase_and_retains_partial_facts(self):
        for phase in ("retrieve", "move_labware", "move_lid"):
            for timing in ("before", "after"):
                with self.subTest(phase=phase, timing=timing):
                    self.assertFailureState(phase, timing, Cancelled("stop"))


if __name__ == "__main__":
    unittest.main()

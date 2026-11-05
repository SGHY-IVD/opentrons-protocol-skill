"""Execute maintained magnetic-supernatant snippets with a recording fixture.

Maintenance only. The planner below supplies controlled test inputs; it is not
a required customer implementation. This is not an Opentrons simulator,
collision model, well-geometry model, or a physical bead-recovery test.
"""
import ast
from bisect import bisect_left
import importlib.util
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('bead_test_rates', ROOT / 'scripts/flow_rate.py')
rates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rates)
TABLES = {
    action: json.loads((ROOT / 'references' / filename).read_text())['rules']
    for action, filename in [('aspirate', 'aspiration-rates.json'),
                             ('dispense', 'dispense-rates.json')]
}


def oracle(action, volume):
    rule = next(r for r in TABLES[action]
                if r['model'] == 'flex_1channel_1000' and r['tip_volume'] == 200
                and r['liquid'] == 'water' and not r.get('filtered', False))
    if not rule['min_rule_volume'] <= volume <= rule['max_volume']:
        raise ValueError('outside maintained curve')
    xs, ys = zip(*rule['points'])
    i = bisect_left(xs, volume)
    if i < len(xs) and xs[i] == volume:
        return float(ys[i])
    if not 0 < i < len(xs):
        raise ValueError('no extrapolation')
    return round(math.fsum((ys[i - 1] * (xs[i] - volume),
                            ys[i] * (volume - xs[i - 1]))) / (xs[i] - xs[i - 1]), 6)


def batches(volume, capacity=200, minimum=5):
    """Controlled planning fixture, checked against frozen boundary outputs."""
    if not all(math.isfinite(x) for x in (volume, capacity, minimum)):
        raise ValueError('finite inputs required')
    if volume < 0 or capacity < 20 or not 0 < minimum <= 20:
        raise ValueError('unsupported input or mode')
    result = []
    remaining = volume
    while remaining > 0:
        body = min(capacity, max(remaining - 20, 0))
        after = remaining - body
        tail = after if 0 < after <= 20 and body + after <= capacity else 0
        following = after - tail
        if following >= remaining:
            raise ValueError('no representable progress')
        result.append((body, tail))
        remaining = following
    if any(0 < part < minimum for batch in result for part in batch):
        raise ValueError('whole-plan minimum-volume failure')
    return result


def code_blocks(filename, heading, following):
    text = (ROOT / 'references' / filename).read_text()
    section = text.split(heading, 1)[1].split(following, 1)[0]
    blocks = re.findall(r'```python\n(.*?)```', section, re.S)
    for block in blocks:
        ast.parse(block)
    return blocks


class Well:
    def __init__(self, name, labware=None):
        self.name, self.labware, self.liquid = name, labware, None

    def top(self, z=0):
        return (self, 'top', z)

    def bottom(self, z=0):
        return (self, 'bottom', z)


class Labware:
    def __init__(self, name, location):
        self.name, self.location, self.wells = name, location, {}

    def __getitem__(self, name):
        if name not in self.wells:
            self.wells[name] = Well(name, self)
        return self.wells[name]

    def load_liquid_by_well(self, volumes, liquid):
        for name, volume in volumes.items():
            self[name].liquid = float(volume)

    def load_liquid(self, wells, volume, liquid):
        for name in wells:
            well = self[name] if isinstance(name, str) else name
            well.liquid = float(volume)


class Pipette:
    def __init__(self, events, capacity=200, minimum=5):
        self.events, self.capacity, self.minimum = events, capacity, minimum
        self.volume, self.has_tip, self.prepared, self.location = 0, False, False, None

    def pick_up_tip(self):
        assert not self.has_tip
        self.has_tip, self.prepared = True, False
        self.events.append(('pick',))

    def prepare_to_aspirate(self):
        assert self.has_tip and self.volume == 0 and self.location[1] == 'top'
        assert not self.prepared, 'unnecessary repeated preparation'
        self.prepared = True
        self.events.append(('prepare',))

    def move_to(self, location, speed=None):
        self.location = location
        self.events.append(('move', location, speed))

    def aspirate(self, volume, location, flow_rate):
        assert self.has_tip and self.prepared
        assert self.minimum <= volume and self.volume + volume <= self.capacity + 1e-9
        well = location[0]
        assert self.location == location and well.liquid is not None
        assert well.liquid + 1e-9 >= volume and math.isfinite(flow_rate) and flow_rate > 0
        before = well.liquid
        well.liquid -= volume
        self.volume += volume
        self.events.append(('aspirate', volume, location, flow_rate, before))

    def dispense(self, volume, location, flow_rate, push_out):
        assert self.has_tip and 0 < volume <= self.volume + 1e-9
        assert math.isfinite(flow_rate) and flow_rate > 0 and push_out == 0
        well = location[0]
        assert well.liquid is not None
        well.liquid += volume
        self.volume -= volume
        self.location = location
        self.events.append(('dispense', volume, location, flow_rate, push_out))

    def drop_tip(self):
        assert self.has_tip and abs(self.volume) < 1e-9
        self.has_tip, self.prepared = False, False
        self.events.append(('drop',))


class Protocol:
    def __init__(self):
        self.events, self.labware, self.pipettes = [], {}, []

    def load_module(self, name, location):
        return SimpleNamespace(name=name, location=location)

    def load_labware(self, name, location):
        item = Labware(name, location)
        self.labware[location] = item
        return item

    def load_trash_bin(self, location):
        return SimpleNamespace(location=location)

    def load_instrument(self, name, mount, tip_racks):
        pipette = Pipette(self.events)
        self.pipettes.append(pipette)
        return pipette

    def define_liquid(self, name, **kwargs):
        return SimpleNamespace(name=name)

    def move_labware(self, labware, new_location, use_gripper):
        assert use_gripper
        labware.location = new_location
        self.events.append(('move_labware', labware, new_location))

    def delay(self, seconds):
        assert seconds > 0 and math.isfinite(seconds)
        self.events.append(('delay', seconds))

    def comment(self, message):
        self.events.append(('comment', message))


class MagneticSupernatantTests(unittest.TestCase):
    def test_frozen_plans(self):
        expected = {
            0: [], 10: [(0, 10)], 20: [(0, 20)], 200: [(180, 20)],
            201: [(181, 0), (0, 20)], 210: [(190, 0), (0, 20)],
            220: [(200, 0), (0, 20)], 400: [(200, 0), (180, 20)],
            410: [(200, 0), (190, 0), (0, 20)],
            450: [(200, 0), (200, 0), (30, 20)]}
        for volume, expected_plan in expected.items():
            self.assertEqual(batches(volume), expected_plan)

    def test_planner_invariants(self):
        # Arithmetic probes across capacities; these are not hardware configurations.
        for capacity in (20, 50, 200, 1000):
            for volume in range(1001):
                plan = batches(volume, capacity, minimum=1)
                self.assertEqual(sum(sum(batch) for batch in plan), volume)
                self.assertTrue(all(0 < sum(batch) <= capacity for batch in plan))
                low = [tail for _, tail in plan if tail]
                self.assertEqual(low, [min(volume, 20)] if volume else [])
                self.assertTrue(not plan or plan[-1][1] > 0)

    def test_invalid_plans_before_actions(self):
        for args in [(-1, 200, 5), (math.nan, 200, 5), (math.inf, 200, 5),
                     (200, 19, 5), (200, 200, 0), (200, 200, 21),
                     (21, 200, 5), (24, 200, 5), (221, 200, 5), (1, 200, 5)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                batches(*args)
        self.assertEqual(batches(25), [(5, 20)])

    def test_actual_pattern_normal_and_water_branches(self):
        block, = code_blocks('patterns-magnetic-supernatant.md',
                             '## 磁吸后去上清单批吸液', '\n## ')
        for volume in (0, 5, 10, 20, 25, 200, 201, 210, 220, 400, 410, 450, 600):
            for dry_run in (False, True):
                with self.subTest(volume=volume, dry_run=dry_run):
                    plan = batches(volume)
                    protocol = Protocol()
                    source = Well('source'); source.liquid = volume
                    waste = Well('waste'); waste.liquid = 0
                    pipette = Pipette(protocol.events)
                    if plan:
                        pipette.pick_up_tip()
                    for index, (body, tail) in enumerate(plan):
                        body_flow = (rates.query('flex_1channel_1000', 200, 'water', body)['flow_rate']
                                     if dry_run and body else 20)
                        tail_flow = (rates.query('flex_1channel_1000', 200, 'water', tail)['flow_rate']
                                     if dry_run and tail else 10)
                        start = len(protocol.events)
                        exec(compile(block, '<maintained-bead-pattern>', 'exec'), {
                            'protocol': protocol, 'pipette': pipette, 'source': source,
                            'body_volume': body, 'tail_volume': tail,
                            'prepare_needed': index == 0, 'body_height': 0.8,
                            'tail_height': 0.1, 'source_entry_speed': 20,
                            'source_exit_speed': 20, 'low_move_speed': 2,
                            'low_settle_delay': 0.2, 'before_aspirate_delay': 0.2,
                            'after_aspirate_delay': 0.2,
                            'after_aspirate_retract_delay': 0,
                            'body_flow': body_flow, 'tail_flow': tail_flow})
                        events = protocol.events[start:]
                        moves = [e for e in events if e[0] == 'move']
                        self.assertEqual(moves[-1][1:], (source.top(), 20))
                        low_moves = [e for e in moves if e[2] == 2]
                        self.assertEqual([e[1] for e in low_moves],
                                         [source.bottom(0.1), source.bottom(0.8)] if tail else [])
                        waits = [e[1] for e in events if e[0] == 'delay']
                        self.assertEqual(waits, [0.2] * ((2 if body else 0) + (2 if tail else 0)))
                        actions = [e for e in events if e[0] == 'aspirate']
                        self.assertEqual([e[1] for e in actions], [x for x in (body, tail) if x])
                        for e in actions:
                            expected = oracle('aspirate', e[1]) if dry_run else (10 if e[2][2] == 0.1 else 20)
                            self.assertAlmostEqual(e[3], expected, places=6)
                            if e[2][2] == 0.1:
                                self.assertEqual(e[4], min(volume, 20))
                        # Controlled external waste step: this test isolates source-side behavior.
                        pipette.dispense(body + tail, waste.top(-3), flow_rate=150, push_out=0)
                    self.assertAlmostEqual(source.liquid, 0)
                    self.assertAlmostEqual(waste.liquid, volume)
                    self.assertEqual(sum(e[0] == 'prepare' for e in protocol.events), bool(plan))

    def test_zero_stage_and_overlapping_wait_requirements(self):
        block, = code_blocks('patterns-magnetic-supernatant.md',
                             '## 磁吸后去上清单批吸液', '\n## ')
        for body, tail, before, after, retract, expected in [
                (0, 0, 0.2, 0.2, 0, []),
                (0, 10, 0.5, 0.1, 0.4, [0.5, 0.1, 0.4]),
                (180, 20, 0, 0, 0, [0.2])]:
            protocol = Protocol()
            source = Well('source'); source.liquid = body + tail
            pipette = Pipette(protocol.events)
            pipette.has_tip = True
            context = dict(protocol=protocol, pipette=pipette, source=source,
                           body_volume=body, tail_volume=tail, prepare_needed=True,
                           body_height=0.8, tail_height=0.1, source_entry_speed=20,
                           source_exit_speed=20, low_move_speed=2, low_settle_delay=0.2,
                           before_aspirate_delay=before, after_aspirate_delay=after,
                           after_aspirate_retract_delay=retract, body_flow=20, tail_flow=10)
            exec(compile(block, '<maintained-bead-waits>', 'exec'), context)
            self.assertEqual([e[1] for e in protocol.events if e[0] == 'delay'], expected)
            if body + tail == 0:
                self.assertEqual(protocol.events, [])

    def test_actual_module_examples(self):
        blocks = code_blocks('module-practices-magnetic-block.md',
                             '### 磁吸后去上清操作示例', '\n### ')
        self.assertEqual(len(blocks), 4)
        for input_index, total, heads in [(1, 200, 1), (2, 460, 2)]:
            protocol = Protocol()
            context = {'protocol': protocol, 'sop_magnetic_seconds': 650}
            for block in (blocks[0], blocks[input_index], blocks[3]):
                exec(compile(block, '<maintained-magnetic-module>', 'exec'), context)
            self.assertEqual(context['waste_well'].liquid, total)
            self.assertTrue(all(w.liquid == 0 for w in context['plate'].wells.values()))
            self.assertIs(context['plate'].location, context['mag'])
            self.assertEqual(sum(e[0] == 'pick' for e in protocol.events), heads)
            self.assertEqual(sum(e[0] == 'prepare' for e in protocol.events), heads)
            self.assertEqual(sum(e[0] == 'drop' for e in protocol.events), heads)
            waits = [e[1] for e in protocol.events if e[0] == 'delay']
            self.assertEqual(waits[:3], [300, 300, 50])
            self.assertTrue(all(t == 0.2 for t in waits[3:]))
            for event in protocol.events:
                if event[0] == 'dispense':
                    self.assertEqual(event[3], oracle('dispense', event[1]))
                elif event[0] == 'aspirate':
                    self.assertEqual(event[3], 10 if event[2][2] == 0.1 else 20)
            self.assertFalse(protocol.pipettes[0].has_tip)
            self.assertEqual(protocol.pipettes[0].volume, 0)


if __name__ == '__main__':
    unittest.main()

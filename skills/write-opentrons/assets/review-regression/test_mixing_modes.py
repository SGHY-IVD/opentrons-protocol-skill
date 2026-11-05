"""Offline mixing-mode contracts, numeric checks, and recording-only actions.

Run: python3 assets/review-regression/test_mixing_modes.py

This is a deliberately local test plan, not a new protocol framework, an SDK
simulation, a real labware model, or a claim about mechanical reachability.
Its supplied piecewise volume/height curve and allowed height interval are
controlled test data. Endpoints express action semantics without guessing a
live API spelling. Flow rates use the existing tool and unchanged JSON; an
independent rational-arithmetic oracle reads those tables. Request-only mode
selection, independent model checks, and a stateful receiver check the plan.
No repository history, expected report, network, or installed SDK is used.
"""
import ast
from bisect import bisect_left
import csv
from dataclasses import dataclass, replace
from decimal import Decimal
from fractions import Fraction
import importlib.util
import io
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_tool(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rates = load_tool('flow_rate.py', 'mix_modes_flow_rate')
delays = load_tool('delay.py', 'mix_modes_delay')
RATE_TABLES = {
    action: json.loads((ROOT / 'references' / filename).read_text())['rules']
    for action, filename in (('aspirate', 'aspiration-rates.json'),
                             ('dispense', 'dispense-rates.json'))}
DELAY_RULES = json.loads((ROOT / 'references' / 'delay-rates.json').read_text())['rules']


def dec(value):
    value = value if isinstance(value, Decimal) else Decimal(str(value))
    if not value.is_finite():
        raise ValueError('finite numeric value required')
    return value


@dataclass(frozen=True)
class ControlledGeometry:
    """Explicit supplied test model; not inferred from depth/capacity alone."""
    depth: Decimal
    capacity: Decimal
    points: tuple
    minimum_z: Decimal = Decimal('0.8')

    def height_from_volume(self, volume):
        volume = dec(volume)
        if not 0 <= volume <= self.capacity:
            raise ValueError('volume outside supplied model')
        for (v0, z0), (v1, z1) in zip(self.points, self.points[1:]):
            if v0 <= volume <= v1:
                return z0 + (z1 - z0) * (volume - v0) / (v1 - v0)
        raise ValueError('missing supplied volume-height interval')

    def checked_z(self, z):
        z = dec(z)
        if not self.minimum_z <= z <= self.depth:
            raise ValueError('height outside already confirmed allowed range')
        return z


def controlled_geometry(depth='30', capacity='1000', minimum_z='0.8'):
    depth, capacity = dec(depth), dec(capacity)
    # This non-linear, explicitly controlled curve prevents volume being
    # mistaken for height, or M/S being substituted for total well volume.
    return ControlledGeometry(depth, capacity,
                              ((dec(0), dec(0)), (capacity / 4, depth / 2),
                               (capacity, depth)), dec(minimum_z))


@dataclass(frozen=True)
class Endpoint:
    kind: str
    z: Decimal
    total_volume: Decimal | None = None
    offset: Decimal = Decimal(0)


@dataclass(frozen=True)
class PathSpec:
    start: Endpoint
    end: Endpoint
    behavior: str


@dataclass(frozen=True)
class LocationSpec:
    """A requested API-like location; surface volume is resolved at the action."""
    kind: str
    z: Decimal = Decimal(0)
    target: str | None = None


def at_bottom(z='.8'):
    return LocationSpec('bottom', dec(z))


def at_meniscus(z=0, target='end'):
    if target not in ('start', 'end', 'dynamic'):
        raise ValueError('unknown meniscus target')
    return LocationSpec('meniscus', dec(z), target)


def bottom(geometry, z):
    return Endpoint('bottom', geometry.checked_z(z))


def surface(geometry, total_volume, offset=0):
    if geometry is None:
        raise ValueError('a supplied volume-height model is required')
    total_volume, offset = dec(total_volume), dec(offset)
    return Endpoint('surface',
                    geometry.checked_z(geometry.height_from_volume(total_volume) + offset),
                    total_volume, offset)


def resolve_path(geometry, operation, volume, before, location, end_location=None, *, nozzles=1):
    """Resolve START/END from the actual ledger and this action's liquid amount.

    DYNAMIC links the two endpoints. This does not model the intermediate
    movement trajectory, and makes no constant-offset claim for a curved well.
    The excluded combination is this task's explicit contract, not SDK proof.
    """
    if not isinstance(location, LocationSpec):
        raise ValueError('a supplied recording location is required')
    if end_location is not None and not isinstance(end_location, LocationSpec):
        raise ValueError('end_location must be a supplied recording location')
    if location.target == 'dynamic' and end_location is not None:
        raise ValueError('dynamic location cannot be combined with explicit end_location')
    if end_location is not None and end_location.target == 'dynamic':
        raise ValueError('dynamic end_location is not an explicit endpoint')
    after = before + nozzles * (volume if operation == 'dispense' else -volume)
    def resolve(request, dynamic_total=None):
        if request.kind == 'bottom':
            return bottom(geometry, request.z)
        if request.kind == 'meniscus':
            total = dynamic_total if request.target == 'dynamic' else (
                before if request.target == 'start' else after)
            return surface(geometry, total, request.z)
        raise ValueError('unsupported recording location')
    if location.target == 'dynamic':
        return PathSpec(resolve(location, before), resolve(location, after), 'endpoint-linked')
    start = resolve(location)
    return PathSpec(start, resolve(end_location) if end_location is not None else start,
                    'moving' if end_location is not None else 'fixed')


@dataclass(frozen=True)
class FixtureInput:
    geometry: ControlledGeometry | None = None
    F: Decimal = Decimal(300)
    model: str = 'flex_8channel_1000'
    tip: int = 200
    mode_capacity: Decimal = Decimal(200)
    ratio: Decimal = Decimal('0.7')
    # Single physical well: explicit stroke needed when its nozzles share inventory.
    nozzles_per_well: int = 1
    mix_volume_per_nozzle: Decimal | None = None
    cycles: int = 3
    mode: str = 'auto'
    liquid: str = 'organic'
    filtered: bool = False
    bottom_z: Decimal = Decimal('0.8')
    # Explicit action positions override defaults without changing selection.
    aspirate_z: Decimal | None = None
    ordinary_dispense_z: Decimal | None = None
    final_z: Decimal | None = None
    push_out: Decimal | None = None
    # A chosen fixture business policy, not a universal dry_run cycle count.
    dry_cycles: int = 1


def sample(**overrides):
    return replace(FixtureInput(geometry=controlled_geometry()), **overrides)


def choose_mode(data, M):
    """Only an explicit whole-mode request can replace the dynamic default.

    ``auto`` means no explicit mode request in this local input vocabulary;
    it is not permission to infer a mode from numeric or geometry fields.
    M remains an argument so callers still pass their final capacity-clipped
    stroke, but selection deliberately does not inspect it.
    """
    if data.mode not in ('auto', 'fixed', 'dynamic'):
        raise ValueError('unknown mixing mode')
    if data.mode != 'auto':
        return data.mode, ('explicit',)
    return 'dynamic', ('default',)


def tail_policy(model, tip):
    """Maintained table instantiated locally, including both 1000uL families."""
    if tip == 20:
        return None
    if tip == 50:
        return dec(10), dec(3 if model.endswith('_50') else 5)
    if tip == 200:
        return dec(20), dec(10)
    if tip == 1000:
        return dec(50), dec(10 if model == 'flex_96channel_1000' else 20)
    raise ValueError('uncovered tip size')


def make_plan(data, dry_run=False):
    """Test-only expansion of a single controlled mixing request."""
    if (type(data.cycles) is not int or data.cycles < 1
            or type(data.dry_cycles) is not int or data.dry_cycles < 1):
        raise ValueError('positive integer cycle counts required')
    F, ratio, available = dec(data.F), dec(data.ratio), min(dec(data.tip), dec(data.mode_capacity))
    if F <= 0 or not 0 < ratio <= 1 or available <= 0:
        raise ValueError('positive volume/capacity and ratio in (0,1] required')
    if data.geometry is None:
        raise ValueError('missing supplied volume-height model; no silent fallback')
    data.geometry.height_from_volume(F)
    n = data.nozzles_per_well
    if type(n) is not int or n < 1:
        raise ValueError('positive confirmed nozzles per physical well required')
    if data.mix_volume_per_nozzle is None:
        if n > 1:
            raise ValueError('shared-well per-nozzle mixing quantity must be established')
        M = min(F * ratio, available)
    else:
        M = dec(data.mix_volume_per_nozzle)
        if not 0 < M <= available:
            raise ValueError('explicit per-nozzle stroke outside available capacity')
    if n * M > F:
        raise ValueError('insufficient aggregate shared-well inventory')
    R, S = M / 10, M * dec('0.9')
    mode, triggers = choose_mode(data, M)
    N = min(data.cycles, data.dry_cycles) if dry_run else data.cycles
    push = dec(data.push_out) if data.push_out is not None else (
        dec({20: 1, 50: 1, 200: 3, 1000: 6}[data.tip]) if data.final_z is None else dec(0))
    if push < 0:
        raise ValueError('push_out must be nonnegative')
    policy = tail_policy(data.model, data.tip)
    T = policy[1] if push and policy is not None and M > policy[0] else dec(0)
    geometry = data.geometry
    base = bottom(geometry, data.bottom_z)
    actions, well, held = [], F, dec(0)
    for index in range(N):
        aspirated = M if index == 0 else S
        post_asp = well - n * aspirated
        if data.aspirate_z is not None:
            point = bottom(geometry, data.aspirate_z)
            asp_path = PathSpec(point, point, 'fixed')
            asp_location = at_bottom(data.aspirate_z)
        elif mode == 'dynamic':
            asp_path = PathSpec(surface(geometry, well, '-0.5'),
                                surface(geometry, post_asp, '-0.5'), 'endpoint-linked')
            asp_location = at_meniscus('-.5', 'dynamic')
        else:
            asp_path = PathSpec(base, base, 'fixed')
            asp_location = at_bottom(data.bottom_z)
        actions.append(dict(operation='aspirate', role='M' if index == 0 else 'S',
                            volume=aspirated, path=asp_path, location=asp_location,
                            end_location=None, cycle=index + 1))
        well, held = post_asp, held + aspirated
        final = index == N - 1
        quantities = [M - T, T] if final and T else [M if final else S]
        previous = base
        for part, quantity in enumerate(quantities):
            post_disp = well + n * quantity
            if final:
                endpoint = (bottom(geometry, data.final_z) if data.final_z is not None
                            else surface(geometry, post_disp))
                path = PathSpec(previous, endpoint, 'moving')
                disp_location = (at_bottom(data.bottom_z) if part == 0 else
                                 at_bottom(data.final_z) if data.final_z is not None else
                                 at_meniscus(0, 'start'))
                disp_end = (at_bottom(data.final_z) if data.final_z is not None else
                            at_meniscus(0, 'end'))
            elif data.ordinary_dispense_z is not None:
                point = bottom(geometry, data.ordinary_dispense_z)
                path = PathSpec(point, point, 'fixed')
                disp_location, disp_end = at_bottom(data.ordinary_dispense_z), None
            elif mode == 'dynamic':
                path = PathSpec(base, surface(geometry, post_disp, '-0.5'), 'moving')
                disp_location, disp_end = at_bottom(data.bottom_z), at_meniscus('-.5', 'end')
            else:
                path = PathSpec(base, base, 'fixed')
                disp_location, disp_end = at_bottom(data.bottom_z), None
            last_part = part == len(quantities) - 1
            action_push = push if final and last_part else dec(0)
            after_held = held - quantity
            if after_held < 0 or (action_push and after_held != 0):
                raise ValueError('nonzero push_out requires empty recorded tip')
            actions.append(dict(operation='dispense',
                                role=('tail' if part else 'body') if final and T else ('final' if final else 'S'),
                                volume=quantity, path=path, push_out=action_push,
                                location=disp_location, end_location=disp_end,
                                cycle=index + 1, intermediate=final and not last_part))
            well, held, previous = post_disp, after_held, path.end
    if well != F or held != 0:
        raise AssertionError('local plan did not conserve liquid')
    # Validate every action in both prepared branches before receiver actions.
    for action in actions:
        action['rates'] = {
            liquid: rates.query(data.model, data.tip, liquid, float(action['volume']),
                                action['operation'], data.filtered)['flow_rate']
            for liquid in set((data.liquid, 'water'))}
    wait = {action: delays.query(data.model, data.tip, data.liquid, action,
                                data.filtered)['phases']
            for action in ('aspirate', 'dispense')}
    return dict(input=data, M=M, R=R, S=S, F=F, T=T, mode=mode,
                triggers=triggers, N=N, actions=actions, wait=wait,
                liquid='water' if dry_run else data.liquid)


class RecordingReceiver:
    """Stateful leaf receiver: volume conservation and endpoint checks only."""
    def __init__(self):
        self.events = []
        self.well = self.held = dec(0)
        self.peak = dec(0)
        self.needs_prepare = False
        self.at_top = True

    def event(self, operation, **details):
        self.events.append(dict(operation=operation, **details))

    def top(self):
        self.at_top = True
        self.event('move_top')

    def prepare(self):
        if self.held != 0 or not self.at_top:
            raise AssertionError('prepare requires an empty tip at this well top')
        self.needs_prepare = False
        self.event('prepare_to_aspirate')

    def apply(self, action, plan):
        operation, volume = action['operation'], action['volume']
        before_well, before_held = self.well, self.held
        path = resolve_path(plan['input'].geometry, operation, volume, before_well,
                            action['location'], action.get('end_location'),
                            nozzles=plan['input'].nozzles_per_well)
        if operation == 'aspirate':
            if self.needs_prepare:
                raise AssertionError('aspirate attempted before required preparation')
            self.well -= plan['input'].nozzles_per_well * volume
            self.held += volume
            if self.well < 0 or self.held > min(plan['input'].tip, plan['input'].mode_capacity):
                raise AssertionError('recorded liquid capacity exceeded')
            self.peak = max(self.peak, self.held)
        else:
            self.well += plan['input'].nozzles_per_well * volume
            self.held -= volume
            if self.held < 0 or (action['push_out'] and self.held):
                raise AssertionError('dispense or push_out with invalid recorded liquid')
            self.needs_prepare = bool(action['push_out'])
        # Check any volume-derived endpoint against the receiver's independent
        # evolving ledger, rather than only comparing two planner fields.
        if path.start.kind == 'surface':
            if path.start.total_volume != before_well:
                raise AssertionError('surface start is not current total well volume')
        if path.end.kind == 'surface' and path.end.total_volume != self.well:
            raise AssertionError('surface end is not resulting total well volume')
        for endpoint in (path.start, path.end):
            if endpoint.kind == 'surface':
                expected_z = plan['input'].geometry.height_from_volume(endpoint.total_volume) + endpoint.offset
                if endpoint.z != expected_z:
                    raise AssertionError('surface endpoint height disagrees with supplied model')
        self.at_top = False
        self.event(operation, **{key: value for key, value in action.items()
                                 if key not in ('operation', 'rates', 'path')}, path=path,
                   flow_rate=action['rates'][plan['liquid']],
                   before_well=before_well, after_well=self.well,
                   before_held=before_held, after_held=self.held)


def add_wait(receiver, phases, phase):
    seconds = phases[phase]['effective_seconds']
    if seconds:
        receiver.event('delay', seconds=seconds, phase=phase)


def execute(plan, receiver, *, continue_same_tip=False):
    if not continue_same_tip:
        receiver.event('liquid_receiver', initial=plan['F'])
        receiver.well = plan['F']
        receiver.event('pick_up_tip')
        receiver.needs_prepare = True
    if receiver.needs_prepare:
        if not receiver.at_top:
            receiver.top()
        receiver.prepare()
        receiver.event('enter', path=plan['actions'][0]['path'].start)
        add_wait(receiver, plan['wait']['aspirate'], 'submerge')
    for action in plan['actions']:
        receiver.apply(action, plan)
        if action.get('intermediate'):
            receiver.event('delay', seconds=0.2, phase='split-intermediate')
        else:
            add_wait(receiver, plan['wait'][action['operation']], 'after')
    receiver.top()
    add_wait(receiver, plan['wait']['dispense'], 'retract')


def run_csv(contents, receiver, dry_run=False):
    plans = []
    for line, row in enumerate(csv.DictReader(io.StringIO(contents)), start=2):
        try:
            geometry = controlled_geometry(row['depth'], row['capacity'])
            data = sample(geometry=geometry, F=dec(row['F']),
                          ratio=dec(row.get('ratio') or '.7'),
                          cycles=int(row.get('cycles') or 3),
                          model=row.get('model') or 'flex_8channel_1000',
                          mode=row.get('mode') or 'auto')
            plans.append(make_plan(data, dry_run))
        except (ValueError, TypeError, KeyError, ArithmeticError) as error:
            raise ValueError(f'CSV row {line}: {error}') from error
    for plan in plans:
        execute(plan, receiver)
    return plans


def curve_oracle(data, liquid, operation, volume):
    """Rational weighted endpoints, independent of the tool's forward scan."""
    candidates = [rule for rule in RATE_TABLES[operation]
                  if (rule['model'], rule['tip_volume'], rule['liquid'],
                      rule.get('filtered', False)) ==
                  (data.model, data.tip, liquid, data.filtered)]
    if len(candidates) != 1:
        raise ValueError('missing independent curve')
    rule = candidates[0]
    actual = Fraction(str(float(volume)))
    if not Fraction(str(rule['min_rule_volume'])) <= actual <= rule['max_volume'] or actual <= 0:
        raise ValueError('outside independent domain')
    coordinates, values = zip(*rule['points'])
    xs = [Fraction(str(item)) for item in coordinates]
    ys = [Fraction(str(item)) for item in values]
    if len(xs) == 1:
        return round(float(ys[0]), 6)
    right = bisect_left(xs, actual)
    if right == len(xs):
        if rule['upper_endpoint'] != 'hold':
            raise ValueError('outside independent curve')
        result = ys[-1]
    elif xs[right] == actual:
        result = ys[right]
    elif right == 0:
        raise ValueError('outside independent curve')
    else:
        left = right - 1
        result = ((xs[right] - actual) * ys[left] +
                  (actual - xs[left]) * ys[right]) / (xs[right] - xs[left])
    return round(float(result), 6)


class DocumentWell:
    """Only the recorded location vocabulary used by the maintained examples."""
    def __init__(self, geometry):
        self.geometry = geometry
        self.depth = float(geometry.depth)
        self.max_volume = float(geometry.capacity)

    def bottom(self, z=0):
        return at_bottom(z)

    def top(self, z=0):
        return LocationSpec('top', dec(z))

    def meniscus(self, z=0, target='end'):
        return at_meniscus(z, target)

    def height_from_volume(self, volume):
        return self.geometry.height_from_volume(volume)


class DocumentPipette:
    """Execute extracted document calls against the same stateful leaf receiver.

    This is a narrow recording adapter, not an SDK implementation. In
    particular, it resolves only operation endpoints, not a motion trajectory.
    """
    def __init__(self, data, receiver):
        self.data = data
        self.receiver = receiver

    @property
    def current_volume(self):
        return float(self.receiver.held)

    def _liquid_action(self, operation, volume, location, flow_rate,
                       end_location=None, push_out=0):
        action = dict(operation=operation, volume=dec(volume), role='document',
                      location=location, end_location=end_location,
                      rates={self.data.liquid: flow_rate}, push_out=dec(push_out))
        self.receiver.apply(action, dict(input=self.data, liquid=self.data.liquid))
        return self

    def aspirate(self, volume, location=None, *, flow_rate, end_location=None):
        return self._liquid_action('aspirate', volume, location, flow_rate, end_location)

    def dispense(self, volume, location=None, *, flow_rate, push_out, end_location=None):
        return self._liquid_action('dispense', volume, location, flow_rate,
                                   end_location, push_out)

    def move_to(self, location, speed=None):
        if location.kind == 'top':
            self.receiver.top()
            self.receiver.events[-1].update(location=location, speed=speed)
        else:
            if location.target not in (None, 'start'):
                raise ValueError('this recording adapter needs an action amount to resolve that target')
            endpoint = (bottom(self.data.geometry, location.z) if location.kind == 'bottom'
                        else surface(self.data.geometry, self.receiver.well, location.z))
            self.receiver.at_top = False
            self.receiver.event('move_to', location=location, endpoint=endpoint, speed=speed)
        return self

    def configure_for_volume(self, volume):
        if self.receiver.held or not self.receiver.at_top:
            raise AssertionError('mode change must be empty at top')
        self.data = replace(self.data, mode_capacity=min(dec(volume), dec(self.data.tip)))
        self.receiver.needs_prepare = True
        self.receiver.event('configure_for_volume', volume=dec(volume))

    def prepare_to_aspirate(self):
        self.receiver.prepare()


class DocumentProtocol:
    def __init__(self, receiver):
        self.receiver = receiver

    def delay(self, *, seconds):
        if not math.isfinite(seconds) or seconds <= 0:
            raise AssertionError('no zero or invalid action wait')
        self.receiver.event('delay', seconds=seconds)


def example_ast(letter):
    """Read current maintained source, never a copied or expected code block."""
    document = (ROOT / 'references' / 'mixing-examples.md').read_text()
    section = next((part for part in document.split('\n## ')
                    if part.startswith(letter + '：') or part.startswith(letter + ':')), None)
    if section is None or '```python\n' not in section:
        raise AssertionError(f'missing maintained {letter} Python example')
    source = section.split('```python\n', 1)[1].split('\n```', 1)[0]
    return ast.parse(source, filename=f'mixing-examples.md:{letter}')


def pattern_ast(heading):
    """Extract the current atomic example instead of copying its actions."""
    document = (ROOT / 'references' / 'patterns-mixing.md').read_text()
    section = document.split(f'\n## {heading}\n', 1)[1].split('\n## ', 1)[0]
    source = section.split('```python\n', 1)[1].split('\n```', 1)[0]
    return ast.parse(source, filename=f'patterns-mixing.md:{heading}')


def execute_example(letter, data, dry_run, *, initial_held=0, context=None):
    receiver = RecordingReceiver()
    receiver.well, receiver.held = data.F, dec(initial_held)
    receiver.at_top = False
    pipette = DocumentPipette(data, receiver)
    namespace = dict(pipette=pipette, protocol=DocumentProtocol(receiver),
                     well=DocumentWell(data.geometry), dry_run=dry_run)
    namespace.update(context or {})
    exec(compile(example_ast(letter), f'<maintained-example-{letter}>', 'exec'), namespace)
    return receiver, namespace


class ModeDecisionTests(unittest.TestCase):
    def assert_dynamic_actions(self, plan):
        self.assertEqual(plan['mode'], 'dynamic')
        for action in plan['actions']:
            if action['operation'] == 'aspirate':
                self.assertEqual(action['location'], at_meniscus('-.5', 'dynamic'))
                self.assertIsNone(action['end_location'])
                self.assertEqual(action['path'].behavior, 'endpoint-linked')
            elif action['role'] == 'S':
                self.assertEqual((action['location'], action['end_location']),
                                 (at_bottom(), at_meniscus('-.5', 'end')))

    def test_default_decision_reads_only_the_requested_mode(self):
        # This input has no F, depth, capacity or model, and M is intentionally
        # nonnumeric: a numeric/geometry routing implementation cannot pass.
        class RequestOnly:
            mode = 'auto'
        self.assertEqual(choose_mode(RequestOnly(), object()), ('dynamic', ('default',)))
        for requested in ('fixed', 'dynamic'):
            RequestOnly.mode = requested
            self.assertEqual(choose_mode(RequestOnly(), object()), (requested, ('explicit',)))
        RequestOnly.mode = 'unrecognized'
        with self.assertRaisesRegex(ValueError, 'unknown mixing mode'):
            choose_mode(RequestOnly(), object())

    def test_default_is_dynamic_across_depth_fill_and_stroke_equalities(self):
        # Cross the former numerical boundaries while checking the requested
        # action semantics against literal locations, not a selection formula.
        table = [
            ('19.999999999', '599.999999999', '.7', 1000),
            ('19.999999999', '600', '.7', 1000),
            ('20', '599.999999999', '.7', 1000),
            ('20', '600', '.7', 1000),
            ('20.000000001', '600.000000001', '.7', 1000),
            ('19.999999999', '799.999999999', '.7', 1000),
            ('19.999999999', '800', '.7', 1000),
            ('19.999999999', '800.000000001', '.7', 1000),
            ('10', '500', '.399999999999', 1000),
            ('10', '500', '.4', 1000),
            ('10', '500', '.400000000001', 1000),
            ('10', '500', '.7', '199.999999999'),
            ('10', '500', '.7', '200'),
            ('10', '500', '.7', '200.000000001'),
        ]
        for depth, F, ratio, capacity in table:
            with self.subTest(depth=depth, F=F, ratio=ratio, available=capacity):
                data = sample(geometry=controlled_geometry(depth), F=dec(F), ratio=dec(ratio),
                              mode_capacity=dec(capacity), tip=1000)
                plan = make_plan(data)
                self.assertEqual(plan['triggers'], ('default',))
                self.assert_dynamic_actions(plan)
                receiver = RecordingReceiver()
                execute(plan, receiver)
                self.assertEqual((receiver.well, receiver.held), (data.F, dec(0)))
                explicit = make_plan(replace(data, mode='dynamic'))
                self.assertEqual(plan['actions'], explicit['actions'])
        # IEEE neighbors must not introduce a hidden display-rounding branch.
        for depth in (math.nextafter(20, -math.inf), 20.0, math.nextafter(20, math.inf)):
            data = sample(geometry=controlled_geometry(depth), F=dec(600), tip=1000,
                          mode_capacity=dec(1000))
            self.assert_dynamic_actions(make_plan(data))

    def test_capacity_clipping_changes_M_R_S_without_selecting_a_mode(self):
        table = [
            (sample(F=dec(600)), (200, 20, 180)),
            (sample(F=dec(500), geometry=controlled_geometry('10'), ratio=dec('.4')),
             (200, 20, 180)),
            (sample(F=dec(400), mode_capacity=dec(120)), (120, 12, 108)),
            (sample(F=dec(300), tip=1000, mode_capacity=dec(1000)), (210, 21, 189)),
        ]
        for data, expected in table:
            for requested in ('auto', 'fixed', 'dynamic'):
                with self.subTest(F=data.F, capacity=data.mode_capacity, requested=requested):
                    plan = make_plan(replace(data, mode=requested))
                    self.assertEqual((plan['M'], plan['R'], plan['S']), tuple(map(dec, expected)))
                    self.assertEqual(plan['mode'], 'fixed' if requested == 'fixed' else 'dynamic')
                    self.assertEqual(plan['N'], data.cycles)
                    self.assertEqual(sum(a['operation'] == 'aspirate' for a in plan['actions']),
                                     data.cycles)

    def test_missing_numeric_selection_data_do_not_waive_independent_model_checks(self):
        for geometry in (None, replace(controlled_geometry(), depth=None),
                         replace(controlled_geometry(), capacity=None)):
            data = sample(geometry=geometry)
            self.assertEqual(choose_mode(data, dec(200)), ('dynamic', ('default',)))
        no_geometry = sample(geometry=None)
        receiver = RecordingReceiver()
        with self.assertRaisesRegex(ValueError, 'model.*no silent fallback'):
            execute(make_plan(no_geometry), receiver)
        self.assertEqual(receiver.events, [])
        # Depth/capacity are not a volume-height curve. Missing intervals and
        # out-of-model volume fail separately after the default is selected.
        for geometry in (replace(controlled_geometry(), points=()),
                         controlled_geometry(capacity='250')):
            data = sample(geometry=geometry)
            self.assertEqual(choose_mode(data, dec(200))[0], 'dynamic')
            receiver = RecordingReceiver()
            with self.assertRaisesRegex(ValueError, 'supplied'):
                execute(make_plan(data), receiver)
            self.assertEqual(receiver.events, [])

    def test_invalid_dynamic_endpoint_cannot_silently_fall_back_to_fixed(self):
        data = sample(F=dec(100), cycles=1, geometry=controlled_geometry('10'))
        self.assertEqual(choose_mode(data, dec(70)), ('dynamic', ('default',)))
        for requested in ('auto', 'dynamic'):
            receiver = RecordingReceiver()
            with self.subTest(requested=requested):
                with self.assertRaisesRegex(ValueError, 'height'):
                    execute(make_plan(replace(data, mode=requested)), receiver)
                self.assertEqual(receiver.events, [])
        # This geometry does permit explicitly requested fixed ordinary
        # actions, proving failure above is not a ban on this entire input.
        fixed = make_plan(replace(data, mode='fixed'))
        self.assertEqual(fixed['mode'], 'fixed')
        receiver = RecordingReceiver()
        execute(fixed, receiver)
        self.assertEqual((receiver.well, receiver.held), (data.F, dec(0)))

    def test_explicit_whole_mode_requests_are_independent_of_geometry_and_ratio(self):
        for requested in ('fixed', 'dynamic'):
            for F, ratio, depth in ((300, '.7', '10'), (800, '.7', '30'),
                                    (500, '.4', '20')):
                with self.subTest(requested=requested, F=F, depth=depth):
                    plan = make_plan(sample(F=dec(F), ratio=dec(ratio), mode=requested,
                                            geometry=controlled_geometry(depth)))
                    self.assertEqual((plan['mode'], plan['triggers']), (requested, ('explicit',)))
                    aspirations = [a for a in plan['actions'] if a['operation'] == 'aspirate']
                    if requested == 'fixed':
                        self.assertTrue(all(a['location'] == at_bottom() for a in aspirations))
                    else:
                        self.assert_dynamic_actions(plan)

    def test_local_position_overrides_do_not_expand_into_whole_mode_requests(self):
        baseline = make_plan(sample())
        cases = [
            ('aspirate_z', dec('1.2')),
            ('ordinary_dispense_z', dec('1.3')),
            ('final_z', dec('2.5')),
        ]
        for key, value in cases:
            with self.subTest(override=key):
                plan = make_plan(sample(**{key: value}))
                self.assertEqual((plan['mode'], plan['triggers']), ('dynamic', ('default',)))
                aspirations = [a for a in plan['actions'] if a['operation'] == 'aspirate']
                ordinary = [a for a in plan['actions']
                            if a['operation'] == 'dispense' and a['role'] == 'S']
                if key == 'aspirate_z':
                    self.assertTrue(all(a['location'] == at_bottom(value) for a in aspirations))
                else:
                    self.assertTrue(all(a['location'] == at_meniscus('-.5', 'dynamic')
                                        for a in aspirations))
                if key == 'ordinary_dispense_z':
                    self.assertTrue(all((a['location'], a['end_location']) == (at_bottom(value), None)
                                        for a in ordinary))
                else:
                    self.assertTrue(all((a['location'], a['end_location']) ==
                                        (at_bottom(), at_meniscus('-.5', 'end')) for a in ordinary))
                if key == 'final_z':
                    self.assertEqual(plan['actions'][-1]['path'].end.z, value)
                    self.assertEqual((plan['T'], plan['actions'][-1]['push_out']), (dec(0), dec(0)))
                else:
                    self.assertEqual(plan['actions'][-2:], baseline['actions'][-2:])
        dynamic = make_plan(sample(mode='dynamic', aspirate_z=dec('1.2'),
                                   ordinary_dispense_z=dec('1.3'), bottom_z=dec('1.1')))
        self.assertEqual(dynamic['mode'], 'dynamic')
        self.assertTrue(all(a['path'].start.z == dec('1.2')
                            for a in dynamic['actions'] if a['operation'] == 'aspirate'))
        ordinary = [a for a in dynamic['actions'] if a['operation'] == 'dispense' and a['role'] == 'S']
        self.assertTrue(all(a['path'].end.z == dec('1.3') for a in ordinary))
        self.assertEqual(dynamic['actions'][-2]['path'].start.z, dec('1.1'))
        explicit = make_plan(sample(final_z=dec('2.5'), push_out=dec(2)))
        self.assertEqual(explicit['actions'][-1]['push_out'], 2)

    def test_one_explicit_action_position_leaves_other_dynamic_actions_intact(self):
        plan = make_plan(sample())
        first, remaining = plan['actions'][0], plan['actions'][1:]
        explicit_location = at_bottom('1.2')
        explicit_path = resolve_path(plan['input'].geometry, 'aspirate', first['volume'],
                                     plan['F'], explicit_location)
        plan['actions'][0] = dict(first, location=explicit_location, path=explicit_path)
        self.assertEqual((plan['mode'], plan['triggers']), ('dynamic', ('default',)))
        self.assertEqual(plan['actions'][1:], remaining)
        self.assertTrue(all(a['location'] == at_meniscus('-.5', 'dynamic')
                            for a in remaining if a['operation'] == 'aspirate'))
        receiver = RecordingReceiver()
        execute(plan, receiver)
        recorded = [e for e in receiver.events if e['operation'] == 'aspirate']
        self.assertEqual(recorded[0]['location'], explicit_location)
        self.assertTrue(all(a['location'] == at_meniscus('-.5', 'dynamic') for a in recorded[1:]))
        self.assertEqual((receiver.well, receiver.held), (plan['F'], dec(0)))


class RecordingAndRateTests(unittest.TestCase):
    def test_meniscus_START_END_use_current_total_and_this_action_amount(self):
        geometry = controlled_geometry()
        # A retained R=20 plus the final S aspiration leaves F-M=100.
        # Body returns 190 -> F-T=290; tail returns 10 -> F=300.
        body = resolve_path(geometry, 'dispense', dec(190), dec(100),
                            at_bottom(), at_meniscus(0, 'end'))
        tail = resolve_path(geometry, 'dispense', dec(10), dec(290),
                            at_meniscus(0, 'start'), at_meniscus(0, 'end'))
        self.assertEqual((body.start.z, body.end.total_volume), (dec('.8'), dec(290)))
        self.assertEqual((tail.start.total_volume, tail.end.total_volume), (dec(290), dec(300)))
        self.assertEqual(tail.start, body.end)
        # Nonlinear supplied curve: endpoint linking is all this receiver
        # asserts. Straight interpolation in z would not stay at -.5 midway.
        dynamic = resolve_path(geometry, 'aspirate', dec(200), dec(300),
                               at_meniscus('-.5', 'dynamic'))
        self.assertEqual((dynamic.start.total_volume, dynamic.end.total_volume), (dec(300), dec(100)))
        interpolated_midpoint_z = (dynamic.start.z + dynamic.end.z) / 2
        actual_midpoint_surface_z = geometry.height_from_volume(dec(200)) - dec('.5')
        self.assertNotEqual(interpolated_midpoint_z, actual_midpoint_surface_z)

    def test_modes_N_1_2_3_5_and_both_runtime_branches_conserve_liquid(self):
        for mode in ('fixed', 'dynamic'):
            for N in (1, 2, 3, 5):
                for dry_run in (False, True):
                    with self.subTest(mode=mode, N=N, dry_run=dry_run):
                        plan = make_plan(sample(mode=mode, cycles=N), dry_run)
                        receiver = RecordingReceiver()
                        execute(plan, receiver)
                        active_N = 1 if dry_run else N
                        liquid = [e for e in receiver.events if e['operation'] in ('aspirate', 'dispense')]
                        aspirations = [e for e in liquid if e['operation'] == 'aspirate']
                        self.assertEqual([a['volume'] for a in aspirations],
                                         [dec(200)] + [dec(180)] * (active_N - 1))
                        dispenses = [e for e in liquid if e['operation'] == 'dispense']
                        self.assertEqual([a['volume'] for a in dispenses],
                                         [dec(180)] * (active_N - 1) + [dec(190), dec(10)])
                        self.assertEqual((receiver.well, receiver.held, receiver.peak),
                                         (dec(300), dec(0), dec(200)))
                        self.assertTrue(all(e['before_well'] + e['before_held'] == dec(300)
                                            and e['after_well'] + e['after_held'] == dec(300)
                                            for e in liquid))
                        self.assertEqual(sum(e['operation'] == 'prepare_to_aspirate' for e in receiver.events), 1)
                        self.assertEqual(sum(e['operation'] == 'move_top' for e in receiver.events), 1)
                        self.assertTrue(receiver.needs_prepare)  # No next aspiration: no redundant prepare.
                        for event in aspirations:
                            path = event['path']
                            if mode == 'dynamic':
                                self.assertEqual(path.behavior, 'endpoint-linked')
                                self.assertEqual((path.start.offset, path.end.offset), (dec('-.5'), dec('-.5')))
                                self.assertLess(path.end.z, path.start.z)
                            else:
                                self.assertEqual((path.start.z, path.end.z), (dec('.8'), dec('.8')))
                        for event in dispenses[:-2]:
                            self.assertEqual(event['push_out'], 0)
                            self.assertEqual(event['path'].start.z, dec('.8'))
                            if mode == 'dynamic':
                                self.assertEqual(event['path'].end.total_volume, dec(280))  # F-R, never S.
                                self.assertEqual(event['path'].end.offset, dec('-.5'))
                            else:
                                self.assertEqual(event['path'].end.z, dec('.8'))
                        body, tail = dispenses[-2:]
                        self.assertEqual((body['path'].start.z, body['path'].end.total_volume),
                                         (dec('.8'), dec(290)))
                        self.assertEqual(tail['path'].start, body['path'].end)
                        self.assertEqual((tail['path'].end.total_volume, tail['path'].end.offset), (dec(300), dec(0)))
                        self.assertEqual((body['push_out'], tail['push_out']), (dec(0), dec(3)))

    def test_all_rate_queries_use_actual_M_S_body_tail_and_six_decimals(self):
        for model, tip, F in (('flex_8channel_50', 20, '20.123456'),
                              ('flex_8channel_50', 50, '50.123456'),
                              ('flex_8channel_1000', 50, '50.123456'),
                              ('flex_8channel_1000', 200, '201.123456'),
                              ('flex_8channel_1000', 1000, '501.123456'),
                              ('flex_96channel_1000', 1000, '501.123456')):
            data = sample(model=model, tip=tip, F=dec(F), mode_capacity=dec(tip), mode='dynamic',
                          geometry=controlled_geometry(capacity=100 if tip <= 50 else 1000))
            for dry_run in (False, True):
                with self.subTest(model=model, tip=tip, dry_run=dry_run):
                    plan = make_plan(data, dry_run)
                    receiver = RecordingReceiver()
                    execute(plan, receiver)
                    for event in receiver.events:
                        if event['operation'] in ('aspirate', 'dispense'):
                            expected = curve_oracle(data, plan['liquid'], event['operation'], event['volume'])
                            self.assertAlmostEqual(event['flow_rate'], expected, places=6)
                            self.assertEqual(event['flow_rate'], round(event['flow_rate'], 6))
        # Water has different rates for these actual quantities. A constant
        # organic dispense curve alone could conceal an M/S/body/tail bug.
        plan = make_plan(sample(F=dec('201.123456'), dry_cycles=3), True)
        by_role = {(a['operation'], a['role']): a['rates']['water'] for a in plan['actions']}
        self.assertNotEqual(by_role['aspirate', 'M'], by_role['aspirate', 'S'])
        self.assertEqual(len({by_role['dispense', key] for key in ('S', 'body', 'tail')}), 3)
        self.assertTrue(any(len(str(rate).split('.')[-1]) == 6 for rate in by_role.values()))

    def test_tail_table_strict_boundaries_and_no_split_conditions(self):
        table = [('flex_8channel_50', 20, '14', '0', '0'),
                 ('flex_8channel_50', 50, '10', '3', '1'),
                 ('flex_8channel_1000', 50, '10', '5', '1'),
                 ('flex_96channel_200', 50, '10', '5', '1'),
                 ('flex_8channel_1000', 200, '20', '10', '3'),
                 ('flex_8channel_1000', 1000, '50', '20', '6'),
                 ('flex_96channel_1000', 1000, '50', '10', '6')]
        for model, tip, threshold, tail, push in table:
            values = (dec(threshold) - dec('.000000001'), dec(threshold),
                      dec(threshold) + dec('.000000001'))
            for volume in values:
                with self.subTest(model=model, tip=tip, M=volume):
                    data = sample(model=model, tip=tip, F=dec(100), ratio=volume / 100,
                                  mode_capacity=dec(tip), cycles=1, mode='fixed')
                    plan = make_plan(data)
                    expected = dec(tail) if tip != 20 and volume > dec(threshold) else dec(0)
                    self.assertEqual(plan['T'], expected)
                    final = [a for a in plan['actions'] if a['operation'] == 'dispense']
                    self.assertEqual(sum(a['volume'] for a in final), volume)
                    self.assertEqual(final[-1]['push_out'], dec(push) if tip != 20 else dec(1))
                    zero_push = make_plan(replace(data, push_out=dec(0)))
                    self.assertEqual(zero_push['T'], 0)

    def test_split_wait_replaces_body_after_without_reentry_or_prepare(self):
        for dry_run in (False, True):
            plan = make_plan(sample(cycles=3), dry_run)
            receiver = RecordingReceiver()
            execute(plan, receiver)
            body_index = next(i for i, e in enumerate(receiver.events) if e.get('role') == 'body')
            self.assertEqual([e['operation'] for e in receiver.events[body_index:body_index + 4]],
                             ['dispense', 'delay', 'dispense', 'delay'])
            self.assertEqual(receiver.events[body_index + 1],
                             dict(operation='delay', seconds=0.2, phase='split-intermediate'))
            self.assertEqual(receiver.events[body_index + 3]['seconds'], 1.0)  # Actual organic after, even dry_run.
            self.assertFalse(any(e['operation'] == 'delay' and e['seconds'] == 0 for e in receiver.events))

    def test_dry_run_reduction_is_fixture_policy_and_waits_keep_actual_liquid(self):
        normal = make_plan(sample(cycles=5))
        reduced = make_plan(sample(cycles=5), True)
        chosen = make_plan(sample(cycles=5, dry_cycles=2), True)
        self.assertEqual((normal['N'], reduced['N'], chosen['N']), (5, 1, 2))
        self.assertEqual(chosen['liquid'], 'water')
        self.assertEqual(chosen['wait'], normal['wait'])
        rule = next(r for r in DELAY_RULES if
                    (r['model'], r['tip_volume'], r['liquid'], r['filtered']) ==
                    ('flex_8channel_1000', 200, 'organic', False))
        for action, raw_name in (('aspirate', 'aspirate'), ('dispense', 'singleDispense')):
            for phase, raw in rule['delays'][raw_name].items():
                self.assertEqual(chosen['wait'][action][phase]['effective_seconds'],
                                 raw['duration'] if raw['enabled'] else 0)

    def test_next_aspiration_prepares_once_at_top_after_final_push(self):
        plan = make_plan(sample(cycles=1))
        receiver = RecordingReceiver()
        execute(plan, receiver)
        count = len(receiver.events)
        execute(plan, receiver, continue_same_tip=True)
        self.assertEqual([e['operation'] for e in receiver.events[count:count + 3]],
                         ['prepare_to_aspirate', 'enter', 'aspirate'])
        self.assertEqual(sum(e['operation'] == 'prepare_to_aspirate' for e in receiver.events), 2)
        receiver.held = dec(1)
        with self.assertRaisesRegex(AssertionError, 'empty tip'):
            receiver.prepare()


class SharedPhysicalWellTests(unittest.TestCase):
    def test_same_per_tip_commands_yield_different_shared_well_endpoints(self):
        geometry = controlled_geometry(capacity='5000', depth='40')
        for n, minimum, ordinary, middle in [(1, 1800, 1980, 1990),
                                              (8, 400, 1840, 1920)]:
            with self.subTest(nozzles_per_well=n):
                plan = make_plan(sample(F=dec(2000), geometry=geometry,
                                        nozzles_per_well=n, mix_volume_per_nozzle=dec(200),
                                        cycles=2, liquid='water'))
                receiver = RecordingReceiver()
                execute(plan, receiver)
                events = [e for e in receiver.events if e['operation'] in ('aspirate', 'dispense')]
                self.assertEqual([e['volume'] for e in events], [200, 180, 180, 190, 10])
                self.assertEqual([e['after_well'] for e in events],
                                 [minimum, ordinary, minimum, middle, 2000])
                self.assertEqual(events[-2]['path'].end, events[-1]['path'].start)
                self.assertEqual(events[-2]['path'].end.z, geometry.height_from_volume(middle))
                self.assertEqual([e['after_held'] for e in events], [200, 20, 200, 10, 0])
                self.assertEqual([e['flow_rate'] for e in events],
                                 [300, 280, 273.333333, 290, 40])

    def test_shared_well_requires_quantity_basis_and_sufficient_instantaneous_inventory(self):
        for M, reason in [(None, 'must be established'), (dec(200), 'aggregate')]:
            receiver = RecordingReceiver()
            with self.assertRaisesRegex(ValueError, reason):
                execute(make_plan(sample(F=dec(300), nozzles_per_well=8,
                                         mix_volume_per_nozzle=M)), receiver)
            self.assertFalse(receiver.events)

    def test_shared_destination_split_uses_each_wells_actual_nozzle_count(self):
        geometry = controlled_geometry(capacity='5000', depth='40')
        for n, middle, final in [(1, 3090, 3100), (8, 3720, 3800)]:
            body = resolve_path(geometry, 'dispense', dec(90), dec(3000),
                                at_bottom(), at_meniscus(0, 'end'), nozzles=n)
            tail = resolve_path(geometry, 'dispense', dec(10), dec(middle),
                                at_meniscus(0, 'start'), at_meniscus(0, 'end'), nozzles=n)
            self.assertEqual(body.end.total_volume, middle)
            self.assertEqual(body.end, tail.start)
            self.assertEqual(tail.end.total_volume, final)


class PreflightAndTransitionTests(unittest.TestCase):
    def test_late_CSV_invalid_row_has_zero_receiver_actions(self):
        header = 'depth,capacity,F,ratio,cycles,model,mode\n'
        valid = '30,1000,300,.7,3,flex_8channel_1000,auto\n'
        failures = [
            '30,1000,NaN,.7,3,flex_8channel_1000,auto\n',
            '30,1000,300,.7,0,flex_8channel_1000,auto\n',
            '30,1000,300,.7,3,unmaintained_model,auto\n',
            '30,1000,1010,.7,3,flex_8channel_1000,auto\n',
            # M=14 is covered; changing-liquid aspiration ends below the
            # already confirmed minimum .8, which must not be clamped.
            '10,1000,20,.7,3,flex_8channel_1000,dynamic\n',
        ]
        for dry_run in (False, True):
            for invalid in failures:
                receiver = RecordingReceiver()
                with self.subTest(dry_run=dry_run, row=invalid):
                    with self.assertRaisesRegex(ValueError, 'CSV row 3'):
                        run_csv(header + valid + invalid, receiver, dry_run)
                    self.assertEqual(receiver.events, [])

    def test_M_can_be_covered_while_actual_S_has_no_water_curve(self):
        contents = 'depth,capacity,F,ratio,cycles,mode\n30,1000,300,.7,3,auto\n30,1000,100,.1,3,fixed\n'
        receiver = RecordingReceiver()
        self.assertEqual(rates.query('flex_8channel_1000', 200, 'water', 10, 'dispense')['flow_rate'], 40)
        with self.assertRaisesRegex(ValueError, 'CSV row 3'):
            run_csv(contents, receiver)
        self.assertEqual(receiver.events, [])
        # In this chosen one-cycle dry_run there is no S action. Its valid
        # M-only plan must not be rejected for an action it will not execute.
        plan = make_plan(sample(F=dec(100), ratio=dec('.1'), mode='fixed'), True)
        self.assertEqual([a['volume'] for a in plan['actions']], [dec(10), dec(10)])

    def test_missing_model_bad_height_and_missing_branch_curve_fail_before_actions(self):
        for data, message in ((sample(geometry=None), 'model'),
                              (sample(geometry=controlled_geometry(minimum_z='1.0')), 'height'),
                              (sample(model='unknown'), '规则缺失')):
            receiver = RecordingReceiver()
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    execute(make_plan(data), receiver)
                self.assertEqual(receiver.events, [])
        original = rates.query
        def missing_water(*args, **kwargs):
            if args[2] == 'water' and args[4] == 'dispense':
                raise ValueError('deliberately missing water curve')
            return original(*args, **kwargs)
        receiver = RecordingReceiver()
        with patch.object(rates, 'query', side_effect=missing_water):
            with self.assertRaisesRegex(ValueError, 'water curve'):
                execute(make_plan(sample()), receiver)
        self.assertEqual(receiver.events, [])

    def test_complete_csv_preflight_precedes_pickup_motion_and_receiver(self):
        contents = 'depth,capacity,F\n30,1000,300\n30,1000,400\n'
        receiver = RecordingReceiver()
        original = make_plan
        calls = []
        def observe(data, dry_run=False):
            self.assertEqual(receiver.events, [])
            calls.append(data.F)
            return original(data, dry_run)
        with patch(__name__ + '.make_plan', side_effect=observe):
            plans = run_csv(contents, receiver)
        self.assertEqual(calls, [dec(300), dec(400)])
        self.assertEqual(len(plans), 2)
        self.assertEqual(receiver.events[0]['operation'], 'liquid_receiver')

    def test_receiver_rejects_dynamic_plus_explicit_end_and_nonzero_push_with_R(self):
        plan = make_plan(sample(mode='dynamic'))
        first = plan['actions'][0]
        wrong = dict(first, end_location=at_meniscus(0, 'end'))
        receiver = RecordingReceiver()
        receiver.well = plan['F']
        with self.assertRaisesRegex(ValueError, 'dynamic location'):
            receiver.apply(wrong, plan)
        self.assertEqual((receiver.well, receiver.held, receiver.events), (plan['F'], dec(0), []))
        with self.assertRaisesRegex(ValueError, 'explicit endpoint'):
            resolve_path(plan['input'].geometry, 'dispense', dec(10), dec(100),
                         at_bottom(), at_meniscus(0, 'dynamic'))
        with self.assertRaisesRegex(ValueError, 'recording location'):
            resolve_path(plan['input'].geometry, 'dispense', dec(10), dec(100),
                         at_bottom(), 'meniscus(end)')
        plan = make_plan(sample())
        first_dispense = next(a for a in plan['actions'] if a['operation'] == 'dispense')
        receiver = RecordingReceiver()
        receiver.well, receiver.held = dec(100), dec(200)
        with self.assertRaisesRegex(AssertionError, 'invalid recorded liquid'):
            receiver.apply(dict(first_dispense, push_out=dec(3)), plan)

class MaintainedExampleTests(unittest.TestCase):
    def assert_document_rates(self, data, actions):
        for action in actions:
            with self.subTest(operation=action['operation'], volume=action['volume']):
                expected = rates.query(data.model, data.tip, data.liquid,
                                       float(action['volume']), action['operation'],
                                       data.filtered)['flow_rate']
                self.assertEqual(action['flow_rate'], expected)
                self.assertAlmostEqual(action['flow_rate'], curve_oracle(
                    data, data.liquid, action['operation'], action['volume']), places=6)

    def test_immediate_addition_default_dynamic_keeps_post_add_ledger_and_continuity(self):
        # Addition changes F and the real clipped M, never the default mode.
        # Equality, geometry and clipping cases all keep the dynamic path;
        # a fixed path has its own explicit whole-mode request.
        table = [
            ('stroke-equality', '10', 480, 20, 200, 'auto', 'dynamic'),
            ('deeper-addition', '30', 550, 50, 1000, 'auto', 'dynamic'),
            ('shallower-addition', '10', 750, 50, 1000, 'auto', 'dynamic'),
            ('capacity-clipped-addition', '10', 490, 20, 200, 'auto', 'dynamic'),
            ('explicit-fixed', '30', 550, 50, 1000, 'fixed', 'fixed'),
            ('explicit-dynamic', '10', 250, 50, 200, 'dynamic', 'dynamic'),
        ]
        addition_ast = pattern_ast('加液后原位立即混匀')
        mixing_ast = pattern_ast('N次手写混匀，保留液与末次排净')
        for name, depth, before, added, tip, requested, expected_mode in table:
            for cycles in (1, 3):
                with self.subTest(case=name, cycles=cycles):
                    before, added = dec(before), dec(added)
                    data = sample(F=before + added, liquid='water', tip=tip,
                                  mode_capacity=dec(tip), mode=requested,
                                  geometry=controlled_geometry(depth))
                    M = min(data.F * data.ratio, dec(data.tip), data.mode_capacity)
                    S = M * dec('.9')
                    selected, _ = choose_mode(data, M)
                    self.assertEqual(selected, expected_mode)
                    if requested == 'auto':
                        pre_M = min(before * data.ratio, dec(tip), data.mode_capacity)
                        self.assertEqual(choose_mode(replace(data, F=before), pre_M),
                                         ('dynamic', ('default',)))
                    def flow(operation, quantity):
                        return rates.query(data.model, data.tip, data.liquid, float(quantity),
                                           operation, data.filtered)['flow_rate']
                    waits = {operation: delays.query(data.model, data.tip, data.liquid,
                                                    operation, data.filtered)['phases']
                             for operation in ('aspirate', 'dispense')}
                    submerge = waits['dispense']['submerge']['effective_seconds']
                    after_add = waits['dispense']['after']['effective_seconds']
                    after_asp = waits['aspirate']['after']['effective_seconds']
                    receiver = RecordingReceiver()
                    receiver.well, receiver.held = before, added
                    well = DocumentWell(data.geometry)
                    entry_speed = {200: 20, 1000: 40}[tip]
                    namespace = dict(
                        pipette=DocumentPipette(data, receiver),
                        protocol=DocumentProtocol(receiver), destination=well, well=well,
                        dynamic_mix=selected == 'dynamic', volume=added, entry_speed=entry_speed,
                        dispense_flow_rate=flow('dispense', added), initial_push_out=0,
                        before_dispense_delay=submerge, after_dispense_delay=after_add,
                        mix_submerge_delay=waits['aspirate']['submerge']['effective_seconds'],
                        mix_cycles=cycles, mix_volume=M, stroke_volume=S,
                        aspirate_full_rate=flow('aspirate', M),
                        aspirate_stroke_rate=flow('aspirate', S),
                        dispense_full_rate=flow('dispense', M),
                        dispense_stroke_rate=flow('dispense', S),
                        aspirate_delay=after_asp, dispense_delay=after_add,
                        ordinary_push_out=0,
                        # This atomic skeleton has not yet expanded split
                        # emptying; the consolidated A/B test covers that expansion.
                        final_push_out={200: 3, 1000: 6}[tip])
                    exec(compile(addition_ast, '<maintained-immediate-addition>', 'exec'), namespace)
                    exec(compile(mixing_ast, '<maintained-following-mix>', 'exec'), namespace)
                    events = receiver.events
                    self.assertEqual([e['operation'] for e in events],
                                     ['move_top', 'move_to', 'delay', 'dispense', 'delay'] +
                                     ['aspirate', 'delay', 'dispense', 'delay'] * cycles)
                    self.assertEqual([e['seconds'] for e in events if e['operation'] == 'delay'],
                                     [submerge, after_add] + [after_asp, after_add] * cycles)
                    actions = [e for e in events if e['operation'] in ('aspirate', 'dispense')]
                    addition, first_aspirate, final = actions[0], actions[1], actions[-1]
                    entry = at_meniscus('-.5', 'start') if selected == 'dynamic' else at_bottom()
                    self.assertEqual(events[1]['location'], entry)
                    self.assertEqual(events[1]['speed'], entry_speed)
                    self.assertEqual((addition['before_well'], addition['after_well'],
                                      addition['before_held'], addition['after_held']),
                                     (before, data.F, added, dec(0)))
                    self.assertEqual(addition['push_out'], 0)
                    self.assertIsNone(addition['end_location'])
                    self.assertEqual(addition['location'],
                                     at_meniscus('-.5', 'dynamic') if selected == 'dynamic'
                                     else at_bottom())
                    if selected == 'dynamic':
                        self.assertEqual((addition['path'].start.total_volume,
                                          addition['path'].end.total_volume), (before, data.F))
                        self.assertEqual((addition['path'].start.offset, addition['path'].end.offset),
                                         (dec('-.5'), dec('-.5')))
                        self.assertEqual((first_aspirate['path'].start.total_volume,
                                          first_aspirate['path'].end.total_volume),
                                         (data.F, data.F - M))
                    else:
                        self.assertEqual((addition['path'].start.z, addition['path'].end.z),
                                         (dec('.8'), dec('.8')))
                    self.assertEqual(addition['path'].end, first_aspirate['path'].start)
                    self.assertEqual([a['volume'] for a in actions if a['operation'] == 'aspirate'],
                                     [M] + [S] * (cycles - 1))
                    self.assertEqual([a['volume'] for a in actions if a['operation'] == 'dispense'],
                                     [added] + [S] * (cycles - 1) + [M])
                    self.assertTrue(all(a['before_well'] + a['before_held'] == data.F
                                        and a['after_well'] + a['after_held'] == data.F for a in actions))
                    self.assert_document_rates(data, actions)
                    self.assertTrue(all(a['push_out'] == 0 for a in actions[:-1]))
                    self.assertEqual((final['path'].start.z, final['path'].end.total_volume,
                                      final['path'].end.offset, final['push_out']),
                                     (dec('.8'), data.F, dec(0), dec({200: 3, 1000: 6}[tip])))
                    self.assertEqual((receiver.well, receiver.held), (data.F, dec(0)))
                    self.assertTrue(receiver.needs_prepare)

    def test_A_B_current_AST_normal_and_dry_run_actual_actions_and_modes(self):
        # Bind the fixture requests to the maintained prose as well as its
        # code: A is an explicit request, B illustrates the default.
        document = (ROOT / 'references' / 'mixing-examples.md').read_text()
        mode_basis = {}
        for line in document.splitlines():
            columns = [column.strip() for column in line.strip().strip('|').split('|')]
            if columns[0] in ('A', 'B'):
                mode_basis[columns[0]] = columns[-1]
        self.assertEqual(mode_basis, {'A': '用户明确静态', 'B': '默认动态'})
        for letter, mode, before, M, R, S in (
                ('A', 'fixed', 100, 140, 14, 126),
                ('B', 'dynamic', 500, 200, 20, 180)):
            for dry_run in (False, True):
                with self.subTest(example=letter, mode=mode, dry_run=dry_run):
                    before, M, R, S = map(dec, (before, M, R, S))
                    F, N = before + 100, 1 if dry_run else 3
                    data = sample(F=before, liquid='water',
                                  mode='fixed' if letter == 'A' else 'auto',
                                  geometry=controlled_geometry('40', '2000'))
                    selected = replace(data, F=F)
                    recommended = F * data.ratio
                    self.assertEqual(recommended, dec(140 if mode == 'fixed' else 420))
                    self.assertEqual(min(recommended, dec(data.tip), data.mode_capacity), M)
                    self.assertEqual((M / 10, M - R), (R, S))
                    self.assertEqual(choose_mode(selected, M)[0], mode)
                    pre_M = min(before * data.ratio, dec(data.tip), data.mode_capacity)
                    self.assertEqual(choose_mode(data, pre_M)[0], mode)
                    self.assertEqual(choose_mode(selected, M)[1],
                                     ('explicit',) if letter == 'A' else ('default',))
                    receiver, namespace = execute_example(letter, data, dry_run, initial_held=100)
                    self.assertEqual(receiver.events, [])  # Definitions have no liquid actions.
                    namespace[f'add_then_{mode}_mix'](
                        namespace['protocol'], namespace['pipette'], namespace['well'], dry_run)
                    events = receiver.events
                    self.assertEqual([e['operation'] for e in events],
                                     ['move_top', 'move_to', 'delay', 'dispense', 'delay'] +
                                     ['aspirate', 'delay', 'dispense', 'delay'] * (N - 1) +
                                     ['aspirate', 'delay', 'dispense', 'delay',
                                      'dispense', 'delay', 'move_top'])
                    actions = [e for e in events if e['operation'] in ('aspirate', 'dispense')]
                    aspirations = [a for a in actions if a['operation'] == 'aspirate']
                    dispenses = [a for a in actions if a['operation'] == 'dispense']
                    self.assertEqual([a['volume'] for a in aspirations], [M] + [S] * (N - 1))
                    self.assertEqual([a['volume'] for a in dispenses],
                                     [dec(100)] + [S] * (N - 1) + [M - 10, dec(10)])
                    self.assertEqual([a['after_held'] for a in actions],
                                     [dec(0)] + [M, R] * (N - 1) + [M, dec(10), dec(0)])
                    self.assertEqual([a['after_well'] for a in actions],
                                     [F] + [F - M, F - R] * (N - 1) + [F - M, F - 10, F])
                    self.assertTrue(all(a['before_well'] + a['before_held'] == F
                                        and a['after_well'] + a['after_held'] == F for a in actions))
                    self.assert_document_rates(data, actions)
                    full_rate, stroke_rate, ordinary_rate, body_rate = (
                        (220, 201.333333, 226, 230) if mode == 'fixed'
                        else (300, 273.333333, 280, 290))
                    expected_rates = [200]
                    for cycle in range(N):
                        expected_rates.append(full_rate if cycle == 0 else stroke_rate)
                        expected_rates.extend([body_rate, 40] if cycle == N - 1 else [ordinary_rate])
                    self.assertEqual([a['flow_rate'] for a in actions], expected_rates)
                    self.assertEqual([e['seconds'] for e in events if e['operation'] == 'delay'],
                                     [.2] * (len(actions) + 1))
                    for operation, phases in (('dispense', ('submerge', 'after')),
                                              ('aspirate', ('after',))):
                        queried = delays.query(data.model, data.tip, data.liquid,
                                               operation, data.filtered)['phases']
                        for phase in phases:
                            self.assertEqual(queried[phase]['effective_seconds'], .2)
                    self.assertEqual((events[0]['location'], events[0]['speed']),
                                     (namespace['well'].top(), None))
                    entry = at_bottom() if mode == 'fixed' else at_meniscus('-.5', 'start')
                    self.assertEqual((events[1]['location'], events[1]['speed']), (entry, 20))
                    self.assertEqual((events[-1]['location'], events[-1]['speed']),
                                     (namespace['well'].top(), 20))
                    addition, body, tail = actions[0], actions[-2], actions[-1]
                    self.assertEqual((addition['before_well'], addition['after_well'],
                                      addition['before_held'], addition['after_held']),
                                     (before, F, dec(100), dec(0)))
                    self.assertEqual(events[1]['endpoint'], addition['path'].start)
                    self.assertEqual(addition['path'].end, aspirations[0]['path'].start)
                    for action in [addition] + aspirations:
                        self.assertIsNone(action['end_location'])
                        if mode == 'dynamic':
                            self.assertEqual(action['location'], at_meniscus('-.5', 'dynamic'))
                            self.assertEqual(action['path'].behavior, 'endpoint-linked')
                            self.assertEqual((action['path'].start.total_volume,
                                              action['path'].end.total_volume),
                                             (action['before_well'], action['after_well']))
                            self.assertEqual((action['path'].start.offset, action['path'].end.offset),
                                             (dec('-.5'), dec('-.5')))
                        else:
                            self.assertEqual(action['location'], at_bottom())
                            self.assertEqual(action['path'], PathSpec(
                                bottom(data.geometry, '.8'), bottom(data.geometry, '.8'), 'fixed'))
                    for action in dispenses[1:-2]:
                        self.assertEqual(action['path'].start.z, dec('.8'))
                        if mode == 'dynamic':
                            self.assertEqual((action['location'], action['end_location']),
                                             (at_bottom(), at_meniscus('-.5', 'end')))
                            self.assertEqual((action['path'].end.total_volume, action['path'].end.offset),
                                             (F - R, dec('-.5')))
                        else:
                            self.assertIsNone(action['end_location'])
                            self.assertEqual(action['path'].end.z, dec('.8'))
                    self.assertEqual((body['location'], body['end_location']),
                                     (at_bottom(), at_meniscus(0, 'end')))
                    self.assertEqual((tail['location'], tail['end_location']),
                                     (at_meniscus(0, 'start'), at_meniscus(0, 'end')))
                    self.assertEqual((body['path'].start.z, body['path'].end.total_volume),
                                     (dec('.8'), F - 10))
                    self.assertEqual(tail['path'].start, body['path'].end)
                    self.assertEqual((tail['path'].end.total_volume, tail['path'].end.offset), (F, dec(0)))
                    self.assertEqual([a['push_out'] for a in actions], [dec(0)] * (len(actions) - 1) + [dec(3)])
                    self.assertEqual((receiver.well, receiver.held, receiver.peak), (F, dec(0), M))
                    self.assertTrue(receiver.at_top)
                    self.assertTrue(receiver.needs_prepare)

    def test_mode_switch_current_pattern_uses_empty_top_and_planned_capacity(self):
        data = sample(F=dec(100), liquid='water', model='flex_8channel_50',
                      tip=50, mode_capacity=dec(30), mode='fixed',
                      geometry=controlled_geometry('11.3', '330'))
        planned = replace(data, mode_capacity=dec(50))
        recommended = data.F * data.ratio
        M = min(recommended, dec(planned.tip), planned.mode_capacity)
        self.assertEqual((recommended, M), (dec(70), dec(50)))
        self.assertEqual(choose_mode(planned, M)[0], 'fixed')
        old_M = min(recommended, dec(data.tip), data.mode_capacity)
        self.assertEqual((old_M, choose_mode(data, old_M)[0]), (dec(30), 'fixed'))
        self.assertEqual(choose_mode(replace(planned, mode='auto'), M),
                         ('dynamic', ('default',)))
        receiver = RecordingReceiver()
        receiver.well, receiver.at_top, receiver.needs_prepare = data.F, False, True
        pipette = DocumentPipette(data, receiver)
        well = DocumentWell(data.geometry)
        retract = delays.query(data.model, data.tip, data.liquid, 'dispense',
                               data.filtered)['phases']['retract']['effective_seconds']
        submerge = delays.query(data.model, data.tip, data.liquid, 'aspirate',
                                data.filtered)['phases']['submerge']['effective_seconds']
        self.assertEqual((retract, submerge), (0, .1))
        namespace = dict(pipette=pipette, protocol=DocumentProtocol(receiver),
                         destination=well, configure_volume=50, dynamic_mix=False,
                         exit_speed=10, entry_speed=10,
                         after_dispense_retract_delay=retract, mix_submerge_delay=submerge)
        tree = pattern_ast('需要切换模式后混匀')
        # Instantiate the actual template's nonzero-delay rule: only its
        # disabled retract placeholder is omitted; every other action remains.
        disabled = [node for node in tree.body
                    if ast.unparse(node) == 'protocol.delay(seconds=after_dispense_retract_delay)']
        self.assertEqual(len(disabled), 1)
        tree.body.remove(disabled[0])
        code = compile(tree, '<maintained-mode-switch>', 'exec')
        exec(code, namespace)
        self.assertEqual([e['operation'] for e in receiver.events],
                         ['move_top', 'configure_for_volume',
                          'prepare_to_aspirate', 'move_to', 'delay'])
        self.assertEqual((receiver.events[0]['location'], receiver.events[0]['speed']),
                         (well.top(), 10))
        self.assertEqual(receiver.events[1]['volume'], dec(50))
        self.assertEqual((receiver.events[3]['location'], receiver.events[3]['speed']),
                         (at_bottom(), 10))
        self.assertEqual([e['seconds'] for e in receiver.events if e['operation'] == 'delay'], [.1])
        self.assertEqual(pipette.data.mode_capacity, dec(50))
        self.assertEqual((receiver.well, receiver.held), (data.F, dec(0)))
        self.assertFalse(receiver.needs_prepare)
        self.assertFalse(receiver.at_top)
        receiver.held = dec(1)
        with self.assertRaisesRegex(AssertionError, 'mode change must be empty at top'):
            exec(code, namespace)


if __name__ == '__main__':
    unittest.main(verbosity=2)

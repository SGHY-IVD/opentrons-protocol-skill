"""Offline numeric regression and a deliberately small mixing/CSV test fixture.

Run: python3 assets/review-regression/test_flow_rate.py

The oracle independently evaluates maintained JSON with binary search and
weighted endpoints. No repository history, network, or installed SDK is needed.
The local three-round recipe and recording receiver below are tests only: they
are neither a protocol framework nor an Opentrons simulator or hardware test.
For numeric M/S coverage this controlled recipe fixes three rounds in both
liquids; it does not test the default dry_run cycle reduction. Branch binding
is covered separately by R251/R252 and the independent generation tests.
"""
import ast
from bisect import bisect_left
import csv
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'flow_rate.py'
MODEL = 'flex_8channel_1000'
TIP = 200


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = load_module(SCRIPT, 'flow_rate_under_test')
TABLES = {
    action: json.loads((ROOT / 'references' / filename).read_text())
    for action, filename in [('aspirate', 'aspiration-rates.json'),
                             ('dispense', 'dispense-rates.json')]
}
RULES = [rule for data in TABLES.values() for rule in data['rules']]


def curve_contract(rule, volume):
    """Independent curve oracle: binary search and two endpoint contributions.

    Validate the maintained domain before classifying exact/interpolated/held
    values. A single-point rule specifies a constant, including when its anchor
    is zero; zero is still an invalid action volume. This uses neither query()
    nor the extracted function, and deliberately avoids their forward scan and
    slope-from-left arithmetic.
    """
    if not math.isfinite(volume) or volume <= 0:
        raise ValueError('体积必须为有限正数')
    if not rule['min_rule_volume'] <= volume <= rule['max_volume']:
        raise ValueError('体积超出已维护规则范围或枪头容量；不外推')
    coordinates, rates = zip(*rule['points'])
    if len(coordinates) == 1:
        return round(rates[0], 6), 'constant'
    right = bisect_left(coordinates, volume)
    if right == len(coordinates):
        if rule['upper_endpoint'] == 'hold':
            return round(rates[-1], 6), 'inherited_official_upper_endpoint'
        raise ValueError('体积超过曲线覆盖范围；不外推')
    if coordinates[right] == volume:
        return round(rates[right], 6), 'exact_point'
    if right == 0:
        raise ValueError('体积低于曲线覆盖范围；不外推')
    left = right - 1
    width = coordinates[right] - coordinates[left]
    contributions = (rates[left] * (coordinates[right] - volume),
                     rates[right] * (volume - coordinates[left]))
    return round(math.fsum(contributions) / width, 6), 'linear_interpolation'


def arguments(rule, volume):
    return (rule['model'], rule['tip_volume'], rule['liquid'], volume,
            rule['action'], rule.get('filtered', False))


def result_or_error(function, *args):
    try:
        return ('result', function(*args))
    except Exception as error:
        return ('error', type(error).__name__, str(error))


def pure_call(function, rule, volume):
    return function(volume, rule['points'], rule['min_rule_volume'],
                    rule['max_volume'], rule['upper_endpoint'])


def rule_name(rule):
    return (rule['model'], rule['tip_volume'], rule['liquid'], rule['action'],
            rule.get('filtered', False))


def interval_probes(rule):
    probes = []
    for left, right in zip(rule['points'], rule['points'][1:]):
        low = max(left[0], rule['min_rule_volume'], 0)
        high = min(right[0], rule['max_volume'])
        if low < high:
            probes.extend(low + (high - low) * fraction
                          for fraction in (0.25, 0.5, 0.75))
    return probes


def boundary_probes(rule):
    values = [rule['min_rule_volume'], rule['max_volume']]
    values.extend(point[0] for point in rule['points'])
    return [probe for value in values for probe in (
        math.nextafter(value, -math.inf), value,
        math.nextafter(value, math.inf))]


def invalid_probes(rule):
    return [0, -1, -0.5, math.nan, math.inf, -math.inf,
            math.nextafter(rule['max_volume'], math.inf),
            rule['tip_volume'] + 1, None, '10']


def all_probes(rule):
    return ([point[0] for point in rule['points']] + interval_probes(rule)
            + boundary_probes(rule) + invalid_probes(rule))


def pure_source(curves=None):
    tree = ast.parse(SCRIPT.read_text())
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef)
                 and node.name == 'interpolate_rate']
    if len(functions) != 1:
        raise AssertionError('Expected exactly one extractable interpolate_rate')
    # Only this import, function, and this task's four literal curves travel.
    module = ast.Module(body=[ast.Import(names=[ast.alias(name='math')]),
                              functions[0]], type_ignores=[])
    source = ast.unparse(ast.fix_missing_locations(module))
    if curves is not None:
        source += '\nCURVES = ' + repr(curves) + '\n'
    return source


def extracted_function(curves=None):
    namespace = {'__name__': 'isolated_rate_fixture'}
    exec(compile(pure_source(curves), '<extracted-rate-function>', 'exec'), namespace)
    return namespace


def selected_curves():
    curves = {}
    for liquid in ('organic', 'water'):
        for action in ('aspirate', 'dispense'):
            matches = [rule for rule in RULES
                       if rule_name(rule) == (MODEL, TIP, liquid, action, False)]
            if len(matches) != 1:
                raise ValueError(f'Missing or duplicate fixture curve: {liquid}/{action}')
            rule = matches[0]
            # This is generation-time validation for this small fixture only.
            if (rule['max_volume'] != TIP
                    or not 0 <= rule['min_rule_volume'] <= TIP
                    or rule['upper_endpoint'] not in ('error', 'hold')
                    or not rule['provenance']
                    or not TABLES[action]['revision']
                    or TABLES[action]['units'] != {'volume': 'uL', 'flow_rate': 'uL/s'}):
                raise ValueError('Invalid selected curve metadata')
            points = rule['points']
            if (not points
                    or any(not math.isfinite(value) for point in points for value in point)
                    or any(rate <= 0 for _, rate in points)
                    or any(a[0] >= b[0] for a, b in zip(points, points[1:]))):
                raise ValueError('Invalid selected curve points')
            curves[(liquid, action)] = {
                key: rule[key] for key in
                ('points', 'min_rule_volume', 'max_volume', 'upper_endpoint')}
    return curves


CURVES = selected_curves()
ISOLATED = extracted_function(CURVES)


def make_mix_plan(volume):
    """Test-only recipe: prefilled F=2V, empty 200uL tip, three mixing rounds.

    The source and receiving liquid are organic in normal mode and water during
    dry_run. Capacity/mode and a valid final meniscus endpoint are controlled
    test state. This does not discover hardware or infer physical reachability.
    """
    if not math.isfinite(volume) or volume <= 0 or volume > TIP:
        raise ValueError('volume must be finite and in (0, 200] uL')
    final = 2 * volume
    raw_m = 0.7 * final
    mix = min(raw_m, TIP)
    retained = 0.1 * mix
    stroke = 0.9 * mix
    split = mix > 20  # Apply the maintained strict threshold before rounding.
    body = mix - 10 if split else mix
    plan = dict(volume=volume, F=final, raw_M=raw_m, M=mix, R=retained,
                S=stroke, body=body, tail=10 if split else 0,
                mid=final - 10 if split else final, split=split, rates={})
    for liquid in ('organic', 'water'):
        rates = {}
        for name, action, actual_volume in (
                ('M_aspirate', 'aspirate', mix),
                ('S_aspirate', 'aspirate', stroke),
                ('S_dispense', 'dispense', stroke),
                ('body_dispense', 'dispense', body)):
            curve = CURVES[(liquid, action)]
            try:
                rates[name] = ISOLATED['interpolate_rate'](
                    actual_volume, curve['points'], curve['min_rule_volume'],
                    curve['max_volume'], curve['upper_endpoint'])
            except ValueError as error:
                raise ValueError(f'{liquid} {name} at {actual_volume} uL: {error}') from error
        if split:
            curve = CURVES[(liquid, 'dispense')]
            rates['tail_dispense'] = ISOLATED['interpolate_rate'](
                10, curve['points'], curve['min_rule_volume'],
                curve['max_volume'], curve['upper_endpoint'])
        plan['rates'][liquid] = rates
    return plan


class RecordingPipette:
    """Leaf action receiver for one recipe; no SDK, geometry, or motion model."""
    def __init__(self):
        self.events = []
        self.held = 0
        self.peak = 0
        self.well = None

    def pick_up_tip(self, initial_well_volume):
        self.well = initial_well_volume
        self.events.append(('pick_up_tip',))

    def prepare_to_aspirate(self):
        if abs(self.held) > 1e-9:
            raise AssertionError('Preparation with retained liquid')
        self.events.append(('prepare_to_aspirate',))

    def aspirate(self, volume, flow_rate):
        self.held += volume
        self.well -= volume
        self.peak = max(self.peak, self.held)
        if self.held > TIP + 1e-9 or self.well < -1e-9:
            raise AssertionError('Fixture liquid capacity exceeded')
        self.events.append(('aspirate', volume, flow_rate))

    def dispense(self, volume, flow_rate, push_out, start=None, end=None):
        self.held -= volume
        self.well += volume
        if self.held < -1e-9 or (push_out and abs(self.held) > 1e-9):
            raise AssertionError('Fixture dispensed absent or retained liquid')
        self.events.append(('dispense', volume, flow_rate, push_out, start, end))

    def delay(self, seconds):
        self.events.append(('delay', seconds))

    def drop_tip(self):
        if abs(self.held) > 1e-9:
            raise AssertionError('Fixture ended with retained liquid')
        self.events.append(('drop_tip',))


def execute_mix_plan(plan, dry_run, receiver):
    # Deliberately explicit fixed three-round local recipe, not a general engine.
    rate = plan['rates']['water' if dry_run else 'organic']
    receiver.pick_up_tip(plan['F'])
    receiver.prepare_to_aspirate()
    receiver.aspirate(plan['M'], rate['M_aspirate'])
    receiver.dispense(plan['S'], rate['S_dispense'], 0)
    receiver.aspirate(plan['S'], rate['S_aspirate'])
    receiver.dispense(plan['S'], rate['S_dispense'], 0)
    receiver.aspirate(plan['S'], rate['S_aspirate'])
    receiver.dispense(plan['body'], rate['body_dispense'],
                      0 if plan['split'] else 3,
                      start='bottom(0.8)', end=plan['mid'])
    if plan['split']:
        receiver.delay(0.2)
        receiver.dispense(plan['tail'], rate['tail_dispense'], 3,
                          start=plan['mid'], end=plan['F'])
    receiver.drop_tip()


def run_csv_fixture(contents, dry_run, receiver):
    # Parse and derive every row before any pick-up. Dependent curve gaps are
    # input failures too, including when only the dry_run water curve has a gap.
    rows = list(csv.DictReader(io.StringIO(contents)))
    plans = []
    for line, row in enumerate(rows, start=2):
        try:
            plans.append(make_mix_plan(float(row['volume'])))
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError(f'CSV row {line}: {error}') from error
    for plan in plans:
        execute_mix_plan(plan, dry_run, receiver)
    return plans


class MaintainedCurveContract(unittest.TestCase):
    def assert_query_contract(self, rule, volume, liquid=None, filtered=None):
        args = list(arguments(rule, volume))
        if liquid is not None:
            args[2] = liquid
        if filtered is not None:
            args[-1] = filtered
        actual = result_or_error(tool.query, *args)
        expected_curve = result_or_error(curve_contract, rule, volume)
        if expected_curve[0] == 'error':
            self.assertEqual(actual, expected_curve)
            return
        self.assertEqual(actual[0], 'result')
        rate, method = expected_curve[1]
        expected_fields = dict(
            flow_rate=rate, units='uL/s', method=method, action=rule['action'],
            filtered=args[-1], model=rule['model'], tip_volume=rule['tip_volume'],
            liquid=rule['liquid'], volume=volume, provenance=rule['provenance'],
            revision=TABLES[rule['action']]['revision'],
            hardware_volume_validation='not_performed')
        self.assertEqual(actual[1].keys(), expected_fields.keys())
        for field, expected in expected_fields.items():
            with self.subTest(field=field):
                self.assertEqual(actual[1][field], expected)

    def test_maintained_table_metadata_and_curve_integrity(self):
        for action, data in TABLES.items():
            with self.subTest(action=action):
                self.assertEqual(data['units'], {'volume': 'uL', 'flow_rate': 'uL/s'})
                self.assertIsInstance(data['revision'], str)
                self.assertTrue(data['revision'])
            for rule in data['rules']:
                with self.subTest(configuration=rule_name(rule)):
                    self.assertEqual(rule['action'], action)
                    self.assertTrue(rule['provenance'])
                    self.assertIn(rule['upper_endpoint'], ('error', 'hold'))
                    self.assertEqual(rule['max_volume'], rule['tip_volume'])
                    self.assertGreaterEqual(rule['min_rule_volume'], 0)
                    self.assertLessEqual(rule['min_rule_volume'], rule['max_volume'])
                    self.assertTrue(rule['points'])
                    for volume, rate in rule['points']:
                        self.assertTrue(math.isfinite(volume))
                        self.assertTrue(math.isfinite(rate))
                        self.assertGreaterEqual(volume, 0)
                        self.assertGreater(rate, 0)
                    coordinates = [point[0] for point in rule['points']]
                    self.assertEqual(coordinates, sorted(set(coordinates)))
                    if len(coordinates) > 1:
                        self.assertEqual(rule['min_rule_volume'], coordinates[0])

    def test_configuration_and_special_case_inventory(self):
        self.assertEqual([len(TABLES[action]['rules']) for action in TABLES], [48, 96])
        self.assertEqual(len(set(map(rule_name, RULES))), 144)
        self.assertEqual(sum(len(rule['points']) for rule in RULES), 398)
        self.assertEqual(sum(len(rule['points']) == 1 for rule in RULES), 42)
        self.assertEqual(sum(len(rule['points']) > 1 and rule['upper_endpoint'] == 'hold'
                             and rule['max_volume'] > rule['points'][-1][0]
                             for rule in RULES), 3)
        self.assertEqual(sum(v > rule['tip_volume'] for rule in RULES
                             for v, _ in rule['points']), 6)

    def test_all_398_anchors_follow_the_maintained_contract(self):
        for rule in RULES:
            for volume, _ in rule['points']:
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    self.assert_query_contract(rule, volume)

    def test_each_legal_interval_at_quarter_midpoint_and_three_quarters(self):
        for rule in RULES:
            for volume in interval_probes(rule):
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    self.assert_query_contract(rule, volume)

    def test_rule_limits_and_every_anchor_at_adjacent_float_boundaries(self):
        for rule in RULES:
            for volume in boundary_probes(rule):
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    self.assert_query_contract(rule, volume)

    def test_invalid_nonfinite_nonnumeric_and_overcapacity_rejections(self):
        for rule in RULES:
            for volume in invalid_probes(rule):
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    self.assert_query_contract(rule, volume)
                    self.assertEqual(result_or_error(tool.query, *arguments(rule, volume))[0],
                                     'error')

    def test_constant_curves_allow_positive_volume_beyond_zero_anchor(self):
        for rule in RULES:
            if len(rule['points']) != 1:
                continue
            for volume in (math.nextafter(0, math.inf), 0.125,
                           rule['max_volume'] / 2, rule['max_volume']):
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    self.assert_query_contract(rule, volume)
                    result = tool.query(*arguments(rule, volume))
                    self.assertEqual(result['method'], 'constant')
                    self.assertEqual(result['flow_rate'], rule['points'][0][1])
            with self.assertRaises(ValueError):
                tool.query(*arguments(rule, 0))

    def test_hold_upper_endpoint_is_preserved_only_within_capacity(self):
        for rule in RULES:
            last = rule['points'][-1][0]
            if len(rule['points']) == 1 or last >= rule['max_volume']:
                continue
            for volume in (math.nextafter(last, math.inf),
                           (last + rule['max_volume']) / 2, rule['max_volume']):
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    self.assert_query_contract(rule, volume)
                    result = tool.query(*arguments(rule, volume))
                    self.assertEqual(result['method'], 'inherited_official_upper_endpoint')
                    self.assertEqual(result['flow_rate'], rule['points'][-1][1])
            with self.assertRaises(ValueError):
                tool.query(*arguments(rule, math.nextafter(rule['max_volume'], math.inf)))

    def test_twenty_ul_capacity_wins_over_fifty_ul_interpolation_anchor(self):
        cases = [(rule, volume) for rule in RULES for volume, _ in rule['points']
                 if volume > rule['tip_volume']]
        self.assertEqual(len(cases), 6)
        for rule, volume in cases:
            with self.subTest(configuration=rule_name(rule), volume=volume):
                self.assertEqual((rule['tip_volume'], volume), (20, 50))
                self.assert_query_contract(rule, volume)
                with self.assertRaisesRegex(ValueError, '枪头容量'):
                    tool.query(*arguments(rule, volume))
                self.assert_query_contract(rule, 20)

    def test_aliases_filter_selection_and_all_output_metadata_match(self):
        aliases = {'water': '水相', 'organic': '有机相', 'glycerol': '甘油相'}
        for rule in RULES:
            volume = (max(rule['min_rule_volume'], 1) + rule['max_volume']) / 2
            with self.subTest(configuration=rule_name(rule)):
                self.assert_query_contract(rule, volume, liquid=aliases[rule['liquid']])
                if rule['action'] == 'aspirate':
                    self.assert_query_contract(rule, volume,
                                               liquid=aliases[rule['liquid']], filtered=True)

    def test_air_gap_defaults_capacity_and_unknown_key_rejections(self):
        configurations = sorted({(rule['model'], rule['tip_volume']) for rule in RULES})
        for model, tip in configurations:
            for volume in (0, 0.125, tip, math.nextafter(tip, math.inf), math.nan):
                args = (model, tip, 'water', volume, 'air_gap', False)
                with self.subTest(model=model, tip=tip, volume=volume):
                    if not math.isfinite(volume) or not 0 < volume <= tip:
                        with self.assertRaises(ValueError):
                            tool.query(*args)
                    else:
                        self.assertEqual(tool.query(*args), dict(
                            flow_rate=20, units='uL/s', method='user_default',
                            action='air_gap', model=model, tip_volume=tip,
                            volume=volume, hardware_volume_validation='not_performed'))
        for args in [('unknown_model', 20, 'water', 10),
                     (MODEL, 123, 'water', 10), (MODEL, TIP, 'unknown_liquid', 10),
                     (MODEL, TIP, 'water', 10, 'unknown_action')]:
            with self.subTest(args=args):
                with self.assertRaisesRegex(ValueError, '规则缺失或重复'):
                    tool.query(*args)


class PureFunction(unittest.TestCase):
    def test_ast_function_matches_query_on_all_configuration_probes(self):
        function = ISOLATED['interpolate_rate']
        for rule in RULES:
            for volume in all_probes(rule):
                with self.subTest(configuration=rule_name(rule), volume=volume):
                    expected = result_or_error(tool.query, *arguments(rule, volume))
                    actual = result_or_error(pure_call, function, rule, volume)
                    if expected[0] == 'result':
                        self.assertEqual(actual, ('result', expected[1]['flow_rate']))
                    else:
                        self.assertEqual(actual, expected)

    def test_independent_known_values_and_six_decimal_rounding(self):
        # Hand-calculated points/slopes, including a declining segment and the
        # 20uL-head 50uL anchor that may help interpolate without enlarging capacity.
        known = [
            ('flex_1channel_50', 20, 'water', 5.5, 'aspirate', 22.5),
            (MODEL, TIP, 'water', 100, 'aspirate', 166.666667),
            (MODEL, TIP, 'water', 100.25, 'aspirate', 167.0),
            (MODEL, TIP, 'water', 150.125, 'aspirate', 233.5),
            (MODEL, TIP, 'water', 130.35, 'dispense', 230.35),
            (MODEL, TIP, 'organic', 130.35, 'dispense', 100),
            ('flex_1channel_50', 50, 'organic', 0.125, 'dispense', 35),
        ]
        for model, tip, liquid, volume, action, expected in known:
            with self.subTest(model=model, tip=tip, liquid=liquid, volume=volume, action=action):
                rule = next(rule for rule in RULES
                            if rule_name(rule) == (model, tip, liquid, action, False))
                self.assertEqual(pure_call(ISOLATED['interpolate_rate'], rule, volume), expected)
                self.assertEqual(tool.query(*arguments(rule, volume))['flow_rate'], expected)
        self.assertEqual(ISOLATED['interpolate_rate'](1.5, [[1, 1], [4, 2]], 1, 4), 1.166667)

    def test_no_lower_extrapolation_and_hold_is_explicit(self):
        function = ISOLATED['interpolate_rate']
        points = [[1, 10], [2, 20]]
        with self.assertRaisesRegex(ValueError, '低于曲线覆盖'):
            function(0.5, points, 0.1, 3)
        with self.assertRaisesRegex(ValueError, '超过曲线覆盖'):
            function(2.5, points, 0.1, 3)
        self.assertEqual(function(2.5, points, 0.1, 3, 'hold'), 20)
        with self.assertRaisesRegex(ValueError, '枪头容量'):
            function(math.nextafter(3, math.inf), points, 0.1, 3, 'hold')

    def test_extracted_namespace_has_only_math_function_and_four_curves(self):
        self.assertEqual(set(ISOLATED), {'__name__', '__builtins__', 'math',
                                        'interpolate_rate', 'CURVES'})
        self.assertEqual(len(ISOLATED['CURVES']), 4)
        self.assertNotIn('__file__', ISOLATED)
        self.assertNotIn('opentrons', ISOLATED)
        with patch('builtins.open', side_effect=AssertionError('Unexpected file access')):
            with patch.object(Path, 'read_text', side_effect=AssertionError('Unexpected table access')):
                for curve in ISOLATED['CURVES'].values():
                    volume = max(curve['min_rule_volume'], 10.125)
                    self.assertTrue(math.isfinite(ISOLATED['interpolate_rate'](
                        volume, curve['points'], curve['min_rule_volume'],
                        curve['max_volume'], curve['upper_endpoint'])))

    def test_standalone_isolated_python_needs_no_skill_directory(self):
        calls = []
        expected = []
        for (liquid, action), curve in CURVES.items():
            for volume in (10.125, 100.25, 150.125, 200):
                calls.append((liquid, action, volume))
                expected.append(tool.query(MODEL, TIP, liquid, volume, action)['flow_rate'])
        source = pure_source(CURVES) + '\nRESULTS = []\n'
        for liquid, action, volume in calls:
            source += (f"c = CURVES[{(liquid, action)!r}]\n"
                       f"RESULTS.append(interpolate_rate({volume!r}, c['points'], "
                       "c['min_rule_volume'], c['max_volume'], c['upper_endpoint']))\n")
        source += 'print(repr(RESULTS))\n'
        self.assertNotIn(str(ROOT), source)
        with tempfile.TemporaryDirectory(prefix='isolated-flow-rate-') as temporary:
            result = subprocess.run([sys.executable, '-I', '-c', source], cwd=temporary,
                                    capture_output=True, text=True, check=True)
        self.assertEqual(ast.literal_eval(result.stdout), expected)
        self.assertEqual(result.stderr, '')

    def test_query_calls_the_same_pure_function_and_retains_method(self):
        for args, expected_method in [
                ((MODEL, TIP, 'water', 100, 'aspirate'), 'linear_interpolation'),
                ((MODEL, TIP, 'water', 200, 'aspirate'), 'exact_point'),
                ((MODEL, TIP, 'organic', 100, 'dispense'), 'constant'),
                ((MODEL, 1000, 'organic', 500, 'aspirate'),
                 'inherited_official_upper_endpoint')]:
            with self.subTest(args=args):
                with patch.object(tool, 'interpolate_rate', wraps=tool.interpolate_rate) as shared:
                    result = tool.query(*args)
                    self.assertEqual(shared.call_count, 1)
                    self.assertEqual(shared.call_args.args[0], args[3])
                    self.assertEqual(result['method'], expected_method)


class LocalParameterAndCSVFixture(unittest.TestCase):
    def test_decimal_plans_have_independent_expected_derived_values(self):
        expected = {
            100.25: (200.5, 140.35, 140.35, 14.035, 126.315, 130.35, 190.5),
            150.125: (300.25, 210.175, 200, 20, 180, 190, 290.25),
        }
        for volume, values in expected.items():
            plan = make_mix_plan(volume)
            for name, value in zip(('F', 'raw_M', 'M', 'R', 'S', 'body', 'mid'), values):
                with self.subTest(volume=volume, derived=name):
                    self.assertAlmostEqual(plan[name], value, places=10)
            self.assertEqual(plan['volume'], volume)
            self.assertEqual(plan['tail'], 10)
        plan = make_mix_plan(100.25)
        self.assertEqual(plan['rates']['water'], {
            'M_aspirate': 220.466667, 'S_aspirate': 201.753333,
            'S_dispense': 226.315, 'body_dispense': 230.35, 'tail_dispense': 40})
        self.assertEqual(plan['rates']['organic'], {
            'M_aspirate': 140.35, 'S_aspirate': 126.315,
            'S_dispense': 100, 'body_dispense': 100, 'tail_dispense': 100})

    def test_every_selected_M_S_body_and_tail_rate_matches_query_in_both_modes(self):
        for volume in (14.28, 14.29, 100.25, 150.125):
            plan = make_mix_plan(volume)
            for dry_run in (False, True):
                receiver = RecordingPipette()
                execute_mix_plan(plan, dry_run, receiver)
                liquid = 'water' if dry_run else 'organic'
                for event in receiver.events:
                    if event[0] in ('aspirate', 'dispense'):
                        with self.subTest(volume=volume, dry_run=dry_run, event=event):
                            expected = tool.query(MODEL, TIP, liquid, event[1], event[0])
                            self.assertEqual(event[2], expected['flow_rate'])
                liquid_events = [event for event in receiver.events
                                 if event[0] in ('aspirate', 'dispense')]
                self.assertEqual([event[0] for event in liquid_events[:5]],
                                 ['aspirate', 'dispense', 'aspirate', 'dispense', 'aspirate'])
                for event, expected_volume in zip(liquid_events[:5],
                                                  (plan['M'], plan['S'], plan['S'],
                                                   plan['S'], plan['S'])):
                    self.assertEqual(event[1], expected_volume)

    def test_receiver_observes_capacity_conservation_and_continuous_final_segments(self):
        for volume in (100.25, 150.125):
            for dry_run in (False, True):
                plan = make_mix_plan(volume)
                receiver = RecordingPipette()
                execute_mix_plan(plan, dry_run, receiver)
                with self.subTest(volume=volume, dry_run=dry_run):
                    self.assertLessEqual(receiver.peak, TIP + 1e-9)
                    self.assertAlmostEqual(receiver.peak, plan['M'])
                    self.assertAlmostEqual(receiver.held, 0)
                    self.assertAlmostEqual(receiver.well, plan['F'])
                    self.assertAlmostEqual(plan['M'], plan['R'] + plan['S'])
                    dispenses = [event for event in receiver.events if event[0] == 'dispense']
                    body, tail = dispenses[-2:]
                    self.assertAlmostEqual(body[1] + tail[1], plan['M'])
                    self.assertEqual((body[3], tail[3]), (0, 3))
                    self.assertEqual((body[4], body[5]), ('bottom(0.8)', plan['F'] - 10))
                    self.assertEqual((tail[4], tail[5]), (body[5], plan['F']))
                    self.assertEqual([event for event in receiver.events if event[0] == 'delay'],
                                     [('delay', 0.2)])
                    self.assertEqual(receiver.events.count(('prepare_to_aspirate',)), 1)

    def test_split_threshold_uses_unrounded_actual_volume_and_reports_derived_gap(self):
        below = make_mix_plan(14.28)  # M=19.992, below 20uL
        equal = make_mix_plan(20 / 1.4)  # This binary-float input derives M=20 exactly.
        above = make_mix_plan(14.29)  # M=20.006, above 20uL
        self.assertFalse(below['split'])
        self.assertEqual(equal['M'], 20)
        self.assertFalse(equal['split'])
        self.assertTrue(above['split'])
        self.assertAlmostEqual(above['body'], 10.006)
        # A value rounding to displayed 20 still crosses the strict threshold.
        near = make_mix_plan(20.00000001 / 1.4)
        self.assertEqual(round(near['M'], 6), 20)
        self.assertTrue(near['split'])
        receiver = RecordingPipette()
        execute_mix_plan(below, True, receiver)
        self.assertFalse(any(event[0] == 'delay' for event in receiver.events))
        self.assertEqual(len([event for event in receiver.events if event[0] == 'dispense']), 3)
        # M=10.5 is covered, but S=9.45 is not covered by the water dispense table.
        self.assertEqual(tool.query(MODEL, TIP, 'water', 10.5, 'dispense')['flow_rate'], 40.75)
        with self.assertRaisesRegex(ValueError, r'water S_dispense at 9\.45\d* uL:.*不外推'):
            make_mix_plan(7.5)

    def test_full_csv_late_invalid_row_is_rejected_before_first_tip_pickup(self):
        for bad in ('nan', 'inf', '-inf', '0', '-1', '200.00001', 'nonnumeric', '7.5'):
            for dry_run in (False, True):
                contents = 'volume\n100.25\n150.125\n' + bad + '\n'
                receiver = RecordingPipette()
                with self.subTest(bad=bad, dry_run=dry_run):
                    with self.assertRaisesRegex(ValueError, 'CSV row 4:'):
                        run_csv_fixture(contents, dry_run, receiver)
                    self.assertEqual(receiver.events, [])
                    self.assertEqual(receiver.held, 0)

    def test_valid_decimal_csv_executes_only_after_all_plans_pass(self):
        contents = 'volume\n100.25\n150.125\n100.25\n'
        for dry_run in (False, True):
            receiver = RecordingPipette()
            with patch(__name__ + '.make_mix_plan', wraps=make_mix_plan) as derive:
                # A pick-up hook proves all three preflight calls finished first.
                original_pickup = receiver.pick_up_tip

                def pick_after_preflight(initial_well_volume):
                    self.assertEqual(derive.call_count, 3)
                    original_pickup(initial_well_volume)

                receiver.pick_up_tip = pick_after_preflight
                plans = run_csv_fixture(contents, dry_run, receiver)
            self.assertEqual([plan['volume'] for plan in plans], [100.25, 150.125, 100.25])
            self.assertEqual(receiver.events.count(('pick_up_tip',)), 3)
            self.assertEqual(receiver.events.count(('drop_tip',)), 3)
            self.assertAlmostEqual(receiver.held, 0)


def coverage_summary():
    return dict(
        oracle='bisect and endpoint-weighted maintained JSON contract; no git history',
        configurations={action: len(data['rules']) for action, data in TABLES.items()},
        anchors=sum(len(rule['points']) for rule in RULES),
        interval_probes=sum(len(interval_probes(rule)) for rule in RULES),
        adjacent_boundary_probes=sum(len(boundary_probes(rule)) for rule in RULES),
        invalid_probes=sum(len(invalid_probes(rule)) for rule in RULES),
        pure_vs_query_probes=sum(len(all_probes(rule)) for rule in RULES),
        standalone_subset_curves=len(CURVES),
        csv_late_invalid_cases=16,
        limitations='Local numeric/recipe receiver checks only; no SDK simulation or hardware.')


if __name__ == '__main__':
    print('Coverage: ' + json.dumps(coverage_summary(), ensure_ascii=False), flush=True)
    unittest.main(verbosity=2)

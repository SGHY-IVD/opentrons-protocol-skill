#!/usr/bin/env python3
"""Validate fixtures or compare review verdicts/locations. Not a protocol analyzer."""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'assets/review-regression'

def read(path):
    return json.loads(Path(path).read_text())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results', type=Path)
    ap.add_argument('--ids', nargs='+', help='Explicit subset of case IDs')
    args = ap.parse_args()
    cases = read(DATA / 'cases.json')['cases']
    answers = read(DATA / 'expected.json')['answers']
    ids = [c['id'] for c in cases]
    assert len(ids) == len(set(ids)) and set(ids) == set(answers), 'Case ID mismatch'
    for case in cases:
        ast.parse(case['code'])
        ans = answers[case['id']]
        assert ans['status'] in ('pass', 'issues', 'unresolved')
        assert (ans['status'] == 'pass') == (not ans['findings'])
        for finding in ans['findings']:
            assert 1 <= finding['line'] <= len(case['code'].splitlines())
            assert finding['reason'].strip()
    selected = set(args.ids or ids)
    assert selected <= set(ids), 'Unknown selected ID'
    if args.results is None:
        print(json.dumps({'fixture_validation': 'pass', 'cases': len(cases)}, ensure_ascii=False))
        return
    rows = read(args.results)['results']
    actual = {r['id']: r for r in rows}
    assert len(actual) == len(rows), 'Duplicate result IDs'
    assert set(actual) == selected, 'Missing or unexpected result IDs'
    differences = []
    for id in sorted(selected):
        exp, got = answers[id], actual[id]
        assert got['status'] in ('pass', 'issues', 'unresolved'), id
        assert isinstance(got['findings'], list), id
        for finding in got['findings']:
            assert isinstance(finding['line'], int) and finding['reason'].strip(), id
        exp_lines = {f['line'] for f in exp['findings']}
        got_lines = {f['line'] for f in got['findings']}
        if got['status'] != exp['status'] or got_lines != exp_lines:
            differences.append({'id': id, 'expected_status': exp['status'],
                'actual_status': got['status'], 'missing_lines': sorted(exp_lines-got_lines),
                'extra_lines': sorted(got_lines-exp_lines)})
    print(json.dumps({'cases': len(selected), 'verdict_location_matches': len(selected)-len(differences),
        'differences': differences,
        'semantic_review': 'REQUIRED: compare reasons, branch conditions and proposed fixes manually; matching lines is not semantic correctness.'}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(differences))

if __name__ == '__main__':
    main()

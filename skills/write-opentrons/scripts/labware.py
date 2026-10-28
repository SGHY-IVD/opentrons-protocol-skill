#!/usr/bin/env python3
"""Search the bundled release index; fetch one definition or rebuild offline."""
import argparse
import ast
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'references' / 'labware-index.json'
REPOSITORY = 'Opentrons/opentrons'
PREFIX = 'shared-data/labware/definitions/'
DEFAULTS_PATH = 'api/src/opentrons/protocol_api/core/engine/_default_labware_versions.py'
LISTING_PATH = 'shared-data/js/getLabware.ts'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_index(path):
    index = read_json(path)
    if (not isinstance(index, dict) or index.get('schema') != 1
            or not isinstance(index.get('source'), dict)
            or index['source'].get('repository') != REPOSITORY
            or not isinstance(index.get('definitions'), list)
            or not all(isinstance(row, dict) for row in index['definitions'])):
        raise ValueError('unsupported index format or repository')
    return scope_index(index)


def blob_sha(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def describe(raw, path, sha):
    parts = Path(path).parts
    definition = json.loads(raw)
    schema = int(parts[0])
    metadata = definition.get('metadata', {})
    if schema == 1:
        return {'legacy_name': metadata['name'], 'schema_version': 1,
                'display_name': metadata['name'], 'source_path': path, 'blob_sha': sha}
    if (schema not in (2, 3) or len(parts) != 3 or
            definition['schemaVersion'] != schema or
            definition['parameters']['loadName'] != parts[1] or
            definition['version'] != int(Path(parts[2]).stem)):
        raise ValueError(f'definition identity/path mismatch: {path}')
    brand = definition.get('brand', {})
    return {
        'load_name': definition['parameters']['loadName'],
        'namespace': definition['namespace'], 'version': definition['version'],
        'schema_version': schema, 'display_name': metadata['displayName'],
        'brand': brand.get('brand', ''), 'catalog_numbers': brand.get('brandId', []),
        'category': metadata.get('displayCategory', ''),
        'roles': definition.get('allowedRoles', []),
        'tags': metadata.get('tags', []), 'source_path': path, 'blob_sha': sha,
    }


def verify_tree(tree):
    """Reconstruct Git trees, including Git's directory sorting/mode encoding."""
    entries = {row['path']: row for row in tree['tree']}
    if tree.get('truncated') is not False or len(entries) != len(tree['tree']):
        raise ValueError('truncated or duplicate Git tree')
    children = {'': []}
    for path, row in entries.items():
        if path.startswith('/') or any(p in ('', '.', '..') for p in path.split('/')):
            raise ValueError('invalid source path')
        parent, _, name = path.rpartition('/')
        if parent and (parent not in entries or entries[parent]['type'] != 'tree'):
            raise ValueError('missing parent tree')
        children.setdefault(parent, []).append((name, row))
        if row['type'] == 'tree':
            children.setdefault(path, [])
    for path, rows in children.items():
        rows = sorted(rows, key=lambda pair: (pair[0] + ('/' if pair[1]['type'] == 'tree' else '')).encode())
        raw = b''.join(row['mode'].lstrip('0').encode() + b' ' + name.encode() + b'\0' +
                       bytes.fromhex(row['sha']) for name, row in rows)
        actual = hashlib.sha1(b'tree ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        expected = tree['sha'] if not path else entries[path]['sha']
        if actual != expected:
            raise ValueError(f'incomplete/changed Git tree: {path or "/"}')


def read_policies(defaults_path, listing_path):
    raw = Path(defaults_path).read_bytes()
    node = next((n for n in ast.parse(raw).body if isinstance(n, ast.AnnAssign)
                 and isinstance(n.target, ast.Name) and n.target.id == 'DEFAULT_LABWARE_VERSIONS'), None)
    if node is None or not isinstance(node.value, ast.Dict):
        raise ValueError('official default-version table not found')
    versions = []
    for key, value in zip(node.value.keys, node.value.values):
        if (not isinstance(key, ast.Call) or not isinstance(key.func, ast.Name)
                or key.func.id != 'APIVersion' or len(key.args) != 2):
            raise ValueError('unhandled official API default-version key')
        versions.append({'api': [ast.literal_eval(v) for v in key.args],
                         'versions': ast.literal_eval(value)})
    listing = Path(listing_path).read_bytes()
    match = re.search(r'export const LABWAREV2_DO_NOT_LIST\s*=\s*new Set\(\[(.*?)\]\)',
                      listing.decode(), flags=re.S)
    if not match:
        raise ValueError('official global labware-listing exclusions not found')
    body = re.sub(r'//[^\n]*', '', match.group(1))
    hidden = sorted(set(re.findall(r"'([^']+)'", body)))
    return {'default_versions': sorted(versions, key=lambda v: v['api']),
            'hidden_from_ui': hidden,
            'sources': [{'path': DEFAULTS_PATH, 'blob_sha': blob_sha(raw)},
                        {'path': LISTING_PATH, 'blob_sha': blob_sha(listing)}]}


def default_version(policy, name, api):
    for boundary in reversed(policy['default_versions']):
        if tuple(api) >= tuple(boundary['api']) and name in boundary['versions']:
            return boundary['versions'][name]
    return 1


def in_flex_scope(row):
    """Local support scope, not a claim of verified Flex compatibility."""
    return (row.get('schema_version') in (2, 3)
            and not re.search(r'\bot[ -]?2\b', row.get('display_name', ''), re.I))


def scope_index(index):
    rows = [r for r in index['definitions'] if in_flex_scope(r)]
    index['definitions'] = rows
    index['source']['scope'] = 'modern definitions excluding explicitly OT-2-labelled items; Flex discovery scope, not compatibility approval'
    index['counts'] = {
        'definitions': len(rows), 'modern_definitions': len(rows), 'legacy_definitions': 0,
        'modern_load_names': len({r['load_name'] for r in rows}),
        'non_default_only_definitions': sum(r.get('non_default_only', False) for r in rows),
        'ordinary_search_load_names': len({r['load_name'] for r in rows
            if not r.get('non_default_only') and not r.get('hidden_from_ui')})}
    return index


def build_index(directory, tree, release, commit, retrieved_on, policy):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', release):
        raise ValueError('use an explicit stable release tag, not edge/main/latest')
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or tree.get('truncated') is not False:
        raise ValueError('a fixed commit and a complete Git tree are required')
    date.fromisoformat(retrieved_on)
    verify_tree(tree)
    rows = []
    for entry in sorted(tree['tree'], key=lambda item: item['path']):
        path = entry['path']
        if entry['type'] != 'blob' or not path.endswith('.json'):
            continue
        if not re.fullmatch(r'(1/[^/]+|[23]/[^/]+/[0-9]+)\.json', path):
            raise ValueError(f'unhandled definition path: {path}')
        raw = (Path(directory) / path).read_bytes()
        if blob_sha(raw) != entry['sha']:
            raise ValueError(f'source blob mismatch: {path}')
        rows.append(describe(raw, path, entry['sha']))
    if not rows or len({r['source_path'] for r in rows}) != len(rows):
        raise ValueError('empty or duplicate definition tree')
    for row in rows:
        if 'load_name' not in row:
            continue
        name = row['load_name']
        defaults = {1, *(p['versions'][name] for p in policy['default_versions'] if name in p['versions'])}
        available = {r['version'] for r in rows if r.get('load_name') == name}
        row['non_default_only'] = not bool(defaults & available)
        row['hidden_from_ui'] = name in policy['hidden_from_ui']
    return scope_index({
        'schema': 1,
        'source': {'repository': REPOSITORY, 'release': release, 'commit': commit,
                   'definitions_tree': tree['sha'], 'retrieved_on': retrieved_on,
                   'scope': 'all JSON definitions in the pinned release tree',
                   'policy_sources': policy['sources']},
        'counts': {'definitions': len(rows),
                   'modern_definitions': sum(r['schema_version'] in (2, 3) for r in rows),
                   'legacy_definitions': sum(r['schema_version'] == 1 for r in rows),
                   'modern_load_names': len({r['load_name'] for r in rows if 'load_name' in r}),
                   'non_default_only_definitions': sum(r.get('non_default_only', False) for r in rows),
                   'ordinary_search_load_names': len({r['load_name'] for r in rows if 'load_name' in r
                        and not r['non_default_only'] and not r['hidden_from_ui']})},
        'default_versions': policy['default_versions'],
        'definitions': rows,
    })


def normalize(text):
    text = text.casefold().replace('µ', 'u').replace('μ', 'u')
    return re.sub(r'[_\-/]+', ' ', text)


def search(index, query, limit=10, include_hidden=False):
    tokens = normalize(query).split()
    if not tokens or limit < 1:
        raise ValueError('provide search words and a positive limit')
    rows = []
    snapshot_matches = 0
    for row in index['definitions']:
        fields = [row.get('load_name', row.get('legacy_name', '')),
                  row['display_name'], row.get('brand', ''), row.get('category', ''),
                  *row.get('catalog_numbers', []), *row.get('tags', [])]
        haystack = normalize(' '.join(fields))
        if all(token in haystack for token in tokens):
            snapshot_matches += 1
            if not include_hidden and (row.get('non_default_only') or row.get('hidden_from_ui')):
                continue
            rows.append(row)
    return {'status': 'candidates' if rows else 'filtered_matches' if snapshot_matches else 'not_found_in_snapshot',
            'source': index['source'], 'total': len(rows), 'returned': min(limit, len(rows)),
            'snapshot_matches': snapshot_matches, 'filtered_matches': snapshot_matches-len(rows),
            'filter_notice': 'filtered rows need explicit --include-hidden investigation; not an incompatibility judgment',
            'definitions': rows[:limit],
            'scope': 'index match only; confirm the actual item, software, geometry and installation'}


def definition_url(index, row):
    source = index['source']
    if source['repository'] != REPOSITORY or not re.fullmatch(r'[0-9a-f]{40}', source['commit']):
        raise ValueError('index must identify the official repository and a fixed commit')
    return f'https://raw.githubusercontent.com/{REPOSITORY}/{source["commit"]}/{PREFIX}{row["source_path"]}'


def get(index, name, version=None, schema=None, namespace='opentrons', api=None):
    if api is not None:
        if version is not None or namespace != 'opentrons':
            raise ValueError('API default lookup is for opentrons names without an explicit version')
        if not re.fullmatch(r'2\.[0-9]+', api):
            raise ValueError('API must be a major.minor version such as 2.30')
        version = default_version(index, name, [int(v) for v in api.split('.')])
    rows = [r for r in index['definitions'] if r.get('load_name') == name
            and r.get('namespace') == namespace
            and (version is None or r['version'] == version)
            and (schema is None or r['schema_version'] == schema)]
    status = ('non_default_only' if rows and all(r.get('non_default_only') for r in rows) else
              'found' if len(rows) == 1 else 'ambiguous' if rows else 'not_found_in_snapshot')
    return {'status': status,
            'selected_api': api, 'selected_version': version,
            'source': index['source'],
            'definitions': [dict(r, definition_url=definition_url(index, r)) for r in rows]}


def fetch(index, source_path, output, timeout=20):
    if not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError('timeout must be finite and in (0, 60] seconds')
    matches = [r for r in index['definitions'] if r['source_path'] == source_path]
    if (len(matches) != 1 or matches[0]['schema_version'] == 1
            or matches[0].get('non_default_only')):
        raise ValueError('select a normal indexed schema 2/3 definition, not legacy or non-default-only test/draft data')
    row = matches[0]
    output = Path(output)
    if output.exists():
        raw = output.read_bytes()
        if blob_sha(raw) != row['blob_sha']:
            raise ValueError('output exists with different content; choose another output path')
        reused = True
    else:
        with urllib.request.urlopen(definition_url(index, row), timeout=timeout) as response:
            raw = response.read()
        reused = False
    if blob_sha(raw) != row['blob_sha']:
        raise ValueError('downloaded blob differs from the indexed release; no definition was saved')
    metadata = describe(raw, source_path, row['blob_sha'])
    if any(row.get(key) != value for key, value in metadata.items()):
        raise ValueError('definition identity/metadata differs from index')
    if not reused:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(raw)
    return {'status': 'reused' if reused else 'downloaded', 'definition_file': str(output.resolve()),
            'definition': row, 'source_url': definition_url(index, row), 'blob_verified': True,
            'scope': 'exact definition retrieved; software availability, models and compatibility need task checks'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, default=DEFAULT_INDEX)
    commands = parser.add_subparsers(dest='command', required=True)
    s = commands.add_parser('search', help='offline keyword search; candidates are not compatibility approval')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=10)
    s.add_argument('--include-hidden', action='store_true', help='include UI-hidden and non-default/test rows for explicit investigation')
    g = commands.add_parser('get', help='offline exact identity lookup; does not silently select versions')
    g.add_argument('load_name')
    g.add_argument('--namespace', default='opentrons')
    g.add_argument('--version', type=int)
    g.add_argument('--schema', type=int, choices=[2, 3])
    g.add_argument('--api', help='resolve the source release default for this API; not software availability proof')
    f = commands.add_parser('fetch', help='explicit network retrieval of one indexed definition')
    f.add_argument('source_path')
    f.add_argument('--output', type=Path, required=True)
    f.add_argument('--timeout', type=float, default=20)
    b = commands.add_parser('build', help='maintenance only: rebuild offline from a complete verified release tree')
    b.add_argument('--definitions', type=Path, required=True)
    b.add_argument('--tree', type=Path, required=True)
    b.add_argument('--default-versions', type=Path, required=True)
    b.add_argument('--listing-policy', type=Path, required=True)
    b.add_argument('--release', required=True)
    b.add_argument('--commit', required=True)
    b.add_argument('--retrieved-on', default=date.today().isoformat())
    b.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'build':
            index = build_index(args.definitions, read_json(args.tree), args.release,
                                args.commit, args.retrieved_on,
                                read_policies(args.default_versions, args.listing_policy))
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(index, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            result = {'status': 'built', 'output': str(args.output.resolve()), 'counts': index['counts']}
        else:
            index = read_index(args.index)
            if args.command == 'search':
                result = search(index, args.query, args.limit, args.include_hidden)
            elif args.command == 'get':
                result = get(index, args.load_name, args.version, args.schema, args.namespace, args.api)
            else:
                result = fetch(index, args.source_path, args.output, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as error:
        print(json.dumps({'status': 'error', 'reason': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

"""Executable lookup/retrieval checks, separate from protocol review fixtures."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('labware_tool', ROOT / 'scripts/labware.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class LabwareLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = tool.read_json(tool.DEFAULT_INDEX)

    def test_offline_brand_catalog_lookup_keeps_all_versions(self):
        with patch.object(tool.urllib.request, 'urlopen', side_effect=AssertionError('offline')):
            result = tool.search(self.index, '201252-100', limit=1)
        self.assertGreater(result['total'], result['returned'])
        self.assertEqual(result['definitions'][0]['load_name'], 'agilent_1_reservoir_290ml')
        self.assertEqual(result['returned'], 1)

    def test_similar_name_is_not_an_exact_identity(self):
        self.assertEqual(tool.get(self.index, 'corning_96_wellplate_330')['status'],
                         'not_found_in_snapshot')
        self.assertEqual(tool.get(self.index, 'corning_96_wellplate_330ul')['status'], 'found')

    def test_versions_are_not_silently_selected(self):
        result = tool.get(self.index, 'nest_96_wellplate_2ml_deep')
        self.assertEqual(result['status'], 'ambiguous')
        self.assertGreater(len(result['definitions']), 1)
        exact = tool.get(self.index, 'nest_96_wellplate_2ml_deep', version=1, schema=2)
        self.assertEqual(exact['status'], 'found')
        self.assertEqual(exact['definitions'][0]['version'], 1)

    def test_api_defaults_follow_official_breakpoints_not_largest_version(self):
        old = tool.get(self.index, 'nest_96_wellplate_2ml_deep', api='2.13')
        current = tool.get(self.index, 'nest_96_wellplate_2ml_deep', api='2.30')
        self.assertEqual(old['definitions'][0]['version'], 1)
        self.assertEqual(current['definitions'][0]['version'], 5)
        self.assertEqual(tool.get(self.index, 'nest_96_wellplate_2ml_deep', api='2.14')
                         ['definitions'][0]['version'], 2)
        with self.assertRaises(ValueError):
            tool.get(self.index, 'nest_96_wellplate_2ml_deep', version=1, api='2.30')

    def test_internal_and_test_rows_are_explicit_not_normal_candidates(self):
        self.assertEqual(tool.search(self.index, 'schema3test')['total'], 0)
        hidden = tool.search(self.index, 'schema3test', include_hidden=True)
        self.assertEqual(hidden['total'], 9)
        self.assertTrue(all(r['non_default_only'] for r in hidden['definitions']))
        self.assertEqual(tool.get(self.index, hidden['definitions'][0]['load_name'])['status'], 'non_default_only')
        self.assertEqual(tool.search(self.index, 'protocol_engine_lid_stack_object')['total'], 0)
        row = hidden['definitions'][0]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                tool.fetch(self.index, row['source_path'], Path(tmp) / 'test.json')

    def test_filtered_matches_are_not_reported_as_snapshot_absence(self):
        filtered = tool.search(self.index, 'eppendorf 10ul')
        self.assertEqual(filtered['status'], 'filtered_matches')
        self.assertGreater(filtered['snapshot_matches'], 0)
        self.assertEqual(filtered['total'], 0)
        explicit = tool.search(self.index, 'eppendorf 10ul', include_hidden=True)
        self.assertEqual(explicit['status'], 'candidates')
        self.assertGreater(explicit['total'], 0)

    def test_absence_only_describes_snapshot(self):
        self.assertEqual(tool.search(self.index, 'nonexistent_987654321')['status'],
                         'not_found_in_snapshot')
        self.assertEqual(tool.get(self.index, 'corning_96_wellplate_330ul',
                                  namespace='custom_beta')['status'], 'not_found_in_snapshot')

    def test_flex_scope_excludes_legacy_and_ot2(self):
        self.assertTrue(all(tool.in_flex_scope(r) for r in self.index['definitions']))
        self.assertTrue(all(tool.in_flex_scope(r) for r in
                            tool.search(self.index, 'OT-2', include_hidden=True)['definitions']))
        self.assertFalse(tool.get(self.index, 'opentrons_96_tiprack_300ul')['definitions'])
        self.assertFalse(tool.in_flex_scope({'schema_version': 1}))
        self.assertFalse(tool.in_flex_scope({'schema_version': 2, 'display_name': 'OT-2 tips'}))
        self.assertTrue(tool.in_flex_scope({'schema_version': 2, 'display_name': 'Generic plate'}))
        self.assertTrue(tool.in_flex_scope({'schema_version': 2, 'display_name': 'Spot 20 plate'}))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                tool.fetch(self.index, '2/opentrons_96_tiprack_300ul/1.json', Path(tmp) / 'old.json')


class ReleaseRetrieval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.definition = {
            'schemaVersion': 2, 'namespace': 'opentrons', 'version': 1,
            'parameters': {'loadName': 'example_1_reservoir_100ul'},
            'metadata': {'displayName': 'Example 1 Reservoir 100 uL'},
        }
        self.raw = json.dumps(self.definition).encode()
        self.path = '2/example_1_reservoir_100ul/1.json'
        self.file = self.directory / self.path
        self.file.parent.mkdir(parents=True)
        self.file.write_bytes(self.raw)
        self.tree = self.make_tree()
        self.policy = {'default_versions': [], 'hidden_from_ui': [], 'sources': []}
        self.index = tool.build_index(self.directory, self.tree, 'v10.0.0', 'a' * 40, '2026-10-28', self.policy)
        self.output = self.directory / 'downloaded.json'

    def make_tree(self):
        def tree_hash(raw):
            return subprocess.run(['git', 'hash-object', '-t', 'tree', '--stdin'], input=raw,
                                  check=True, capture_output=True).stdout.decode().strip()
        parts = self.path.split('/')
        leaf = tool.blob_sha(self.raw)
        middle = tree_hash(b'100644 ' + parts[2].encode() + b'\0' + bytes.fromhex(leaf))
        top = tree_hash(b'40000 ' + parts[1].encode() + b'\0' + bytes.fromhex(middle))
        root = tree_hash(b'40000 ' + parts[0].encode() + b'\0' + bytes.fromhex(top))
        return {'sha': root, 'truncated': False, 'tree': [
            {'path': parts[0], 'type': 'tree', 'mode': '040000', 'sha': top},
            {'path': '/'.join(parts[:2]), 'type': 'tree', 'mode': '040000', 'sha': middle},
            {'path': self.path, 'type': 'blob', 'mode': '100644', 'sha': leaf}]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_rebuild_filters_ot2_after_verifying_source(self):
        self.definition['metadata']['displayName'] = 'Opentrons OT-2 Test Tips'
        self.raw = json.dumps(self.definition).encode()
        self.file.write_bytes(self.raw)
        tree = self.make_tree()
        index = tool.build_index(self.directory, tree, 'v10.0.0', 'a' * 40,
                                 '2026-10-28', self.policy)
        self.assertEqual(index['counts']['definitions'], 0)
        self.file.write_bytes(self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'blob mismatch'):
            tool.build_index(self.directory, tree, 'v10.0.0', 'a' * 40,
                             '2026-10-28', self.policy)

    def test_imported_index_cannot_restore_out_of_scope_entries(self):
        index = json.loads(json.dumps(self.index))
        row = dict(index['definitions'][0], display_name='OT-2 Test Tips')
        index['definitions'].append(row)
        file = self.directory / 'imported-index.json'
        file.write_text(json.dumps(index))
        scoped = tool.read_index(file)
        self.assertEqual(scoped['counts']['definitions'], 1)
        self.assertTrue(all(tool.in_flex_scope(r) for r in scoped['definitions']))

    def test_pinned_fetch_and_reuse_preserve_exact_bytes(self):
        with patch.object(tool.urllib.request, 'urlopen', return_value=io.BytesIO(self.raw)) as network:
            result = tool.fetch(self.index, self.path, self.output)
        self.assertTrue(result['blob_verified'])
        self.assertEqual(self.output.read_bytes(), self.raw)
        self.assertIn('/' + 'a' * 40 + '/', network.call_args.args[0])
        with patch.object(tool.urllib.request, 'urlopen', side_effect=AssertionError('reuse must be offline')):
            self.assertEqual(tool.fetch(self.index, self.path, self.output)['status'], 'reused')

    def test_network_failure_leaves_no_definition(self):
        with patch.object(tool.urllib.request, 'urlopen', side_effect=URLError('unavailable')):
            with self.assertRaises(URLError):
                tool.fetch(self.index, self.path, self.output)
        self.assertFalse(self.output.exists())

    def test_hash_mismatch_is_not_saved(self):
        with patch.object(tool.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"other":true}')):
            with self.assertRaisesRegex(ValueError, 'blob differs'):
                tool.fetch(self.index, self.path, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_different_file_is_preserved(self):
        self.output.write_bytes(b'user definition')
        with patch.object(tool.urllib.request, 'urlopen', side_effect=AssertionError('no download')):
            with self.assertRaisesRegex(ValueError, 'different content'):
                tool.fetch(self.index, self.path, self.output)
        self.assertEqual(self.output.read_bytes(), b'user definition')

    def test_rebuild_rejects_incomplete_and_changed_sources(self):
        self.tree['truncated'] = True
        with self.assertRaises(ValueError):
            tool.build_index(self.directory, self.tree, 'v10.0.0', 'a' * 40, '2026-10-28', self.policy)
        self.tree['truncated'] = False
        self.file.write_bytes(self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'blob mismatch'):
            tool.build_index(self.directory, self.tree, 'v10.0.0', 'a' * 40, '2026-10-28', self.policy)
        self.file.unlink()
        with self.assertRaises(FileNotFoundError):
            tool.build_index(self.directory, self.tree, 'v10.0.0', 'a' * 40, '2026-10-28', self.policy)

    def test_untruncated_flag_does_not_excuse_a_missing_tree_entry(self):
        self.tree['tree'].pop()
        with self.assertRaisesRegex(ValueError, 'Git tree'):
            tool.build_index(self.directory, self.tree, 'v10.0.0', 'a' * 40, '2026-10-28', self.policy)

    def test_rebuild_requires_stable_release_and_consistent_identity(self):
        with self.assertRaises(ValueError):
            tool.build_index(self.directory, self.tree, 'edge', 'a' * 40, '2026-10-28', self.policy)
        self.definition['version'] = 2
        self.raw = json.dumps(self.definition).encode()
        self.file.write_bytes(self.raw)
        self.tree = self.make_tree()
        with self.assertRaisesRegex(ValueError, 'identity/path mismatch'):
            tool.build_index(self.directory, self.tree, 'v10.0.0', 'a' * 40, '2026-10-28', self.policy)

    def test_successful_retrieval_does_not_claim_models_or_compatibility(self):
        with patch.object(tool.urllib.request, 'urlopen', return_value=io.BytesIO(self.raw)):
            result = tool.fetch(self.index, self.path, self.output)
        self.assertNotIn('innerLabwareGeometry', json.loads(self.output.read_bytes()))
        self.assertNotIn('compatible', result)

    def test_invalid_index_and_timeout_fail_without_network(self):
        invalid = self.directory / 'invalid-index.json'
        for value in ([], None, {'schema': 999}, {'schema': 1, 'source': None}):
            invalid.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'unsupported index'):
                tool.read_index(invalid)
        with patch.object(tool.urllib.request, 'urlopen', side_effect=AssertionError('no request')):
            for timeout in (float('inf'), float('nan'), 0, -1, 61):
                with self.assertRaises(ValueError):
                    tool.fetch(self.index, self.path, self.output, timeout)
        self.assertFalse(self.output.exists())

    def test_schema_three_is_not_itself_a_test_or_compatibility_verdict(self):
        self.file.unlink()
        self.definition['schemaVersion'] = 3
        self.raw = json.dumps(self.definition).encode()
        self.path = self.path.replace('2/', '3/', 1)
        self.file = self.directory / self.path
        self.file.parent.mkdir(parents=True)
        self.file.write_bytes(self.raw)
        index = tool.build_index(self.directory, self.make_tree(), 'v10.0.0', 'a' * 40,
                                 '2026-10-28', self.policy)
        self.assertFalse(index['definitions'][0]['non_default_only'])
        self.assertEqual(tool.search(index, 'example')['total'], 1)


if __name__ == '__main__':
    unittest.main()

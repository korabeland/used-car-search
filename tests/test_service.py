import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import http.client
import json
import threading

path = Path(__file__).resolve().parents[1] / 'service' / 'server.py'
spec = importlib.util.spec_from_file_location('car_service', path)
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)
VIN = '1HGCM82633A004352'

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = service.Store(Path(self.temp.name) / 'test.sqlite')

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def test_import_idempotent_and_decisions_preserved(self):
        batch = {'vehicles': [{'vin': VIN, 'asking_price': 24000, 'scores': {'history': 15}}]}
        self.assertEqual(self.store.import_batch(batch)['changed'], 1)
        self.store.decision(dict(entity_id=VIN, decision='hold', note='Need report', gate='shortlist'))
        count = len(self.store.state()['changes'])
        self.assertEqual(self.store.import_batch(batch)['changed'], 0)
        self.assertEqual(len(self.store.state()['changes']), count)
        self.store.import_batch({'vehicles': [{'vin': VIN, 'asking_price': 23500}]})
        state = self.store.state()
        self.assertEqual(len(state['decisions']), 1)
        self.assertEqual(state['vehicles'][0]['scores'], {'history': 15})

    def test_invalid_batch_is_atomic(self):
        with self.assertRaises(ValueError):
            self.store.import_batch({'dealers': [{'id': 'dealer-one'}], 'vehicles': [{'vin': 'invalid'}]})
        self.assertEqual(self.store.state()['dealers'], [])

    def test_unknown_scores_and_validation(self):
        self.assertEqual(service.score({}), dict(earned=0, checkable=0, coverage=0, max=100))
        self.assertEqual(service.score({'history': 15, 'service': None}), dict(earned=15, checkable=18, coverage=18, max=97))
        for bad in ({'history': 19}, {'price': -1}, {'other': 0}, {'history': True}):
            with self.assertRaises(ValueError):
                service.score(bad)

    def test_state_exposes_rubric_and_summary_without_stage(self):
        self.store.import_batch({'vehicles': [{'vin': VIN, 'scores': {'history': 15, 'fit': 7}}]})
        state = self.store.state()
        self.assertEqual(state['rubric'], service.DEFAULT_CONFIG['weights'])
        self.assertIn('fit', state['rubric'])
        self.assertNotIn('stage', state)
        self.assertIsNotNone(state['updated_at'])
        vehicle = state['vehicles'][0]
        self.assertEqual(vehicle['score_summary'], dict(earned=22, checkable=25, coverage=25, max=97, maximum=97))
        self.assertEqual(vehicle['score'], dict(earned=22, checkable=25, coverage=25, max=97))

    def test_custom_weights_change_max_and_coverage(self):
        weights = {'a': 20, 'b': 30}
        self.assertEqual(service.score({'a': 15}, weights), dict(earned=15, checkable=20, coverage=40, max=45))
        self.assertEqual(service.score({}, weights), dict(earned=0, checkable=0, coverage=0, max=50))
        self.assertEqual(service.score({'a': 20, 'b': 30}, weights), dict(earned=50, checkable=50, coverage=100, max=50))
        rounded = service.score({'a': 1}, {'a': 10, 'b': 20})
        self.assertEqual(rounded['coverage'], 33)
        self.assertIsInstance(rounded['coverage'], int)
        for bad in ({'history': 1}, {'a': 21}):
            with self.assertRaises(ValueError):
                service.score(bad, weights)

    def test_store_uses_configured_weights(self):
        weights = {'a': 20, 'b': 30}
        store = service.Store(Path(self.temp.name) / 'custom.sqlite', dict(weights=weights, critical_fields=[]))
        try:
            store.import_batch({'vehicles': [{'vin': VIN, 'scores': {'a': 15}}]})
            state = store.state()
            self.assertEqual(state['rubric'], weights)
            self.assertEqual(state['vehicles'][0]['score_summary'],
                             dict(earned=15, checkable=20, coverage=40, max=45, maximum=45))
            with self.assertRaises(ValueError):
                store.import_batch({'vehicles': [{'vin': VIN, 'scores': {'history': 5}}]})
            with self.assertRaises(ValueError):
                store.import_batch({'vehicles': [{'vin': VIN, 'scores': {'a': 21}}]})
        finally:
            store.db.close()

    def test_conflicts_preserve_evidence_and_are_idempotent(self):
        self.store.import_batch({'vehicles': [{'vin': VIN, 'drivetrain': 'AWD'}]})
        change = {'vehicles': [{'vin': VIN, 'drivetrain': 'FWD'}]}
        self.store.import_batch(change)
        row = self.store.state()['vehicles'][0]
        self.assertEqual(row['drivetrain'], 'AWD')
        self.assertEqual(row['conflicts'][0]['incoming'], 'FWD')
        self.assertEqual(row['review_status'], 'Needs conflict review')
        self.assertEqual(self.store.import_batch(change)['changed'], 0)

    def test_only_configured_critical_fields_are_conflict_protected(self):
        store = service.Store(Path(self.temp.name) / 'critical.sqlite',
                              dict(weights={'a': 1}, critical_fields=['color']))
        try:
            store.import_batch({'vehicles': [{'vin': VIN, 'color': 'black', 'mileage': 100, 'drivetrain': 'AWD'}]})
            store.import_batch({'vehicles': [{'vin': VIN, 'color': 'red', 'mileage': 200, 'drivetrain': 'FWD'}]})
            row = store.state()['vehicles'][0]
            self.assertEqual(row['color'], 'black')
            self.assertEqual(row['conflicts'], [dict(field='color', previous='black', incoming='red')])
            self.assertEqual(row['review_status'], 'Needs conflict review')
            self.assertEqual(row['mileage'], 200)
            self.assertEqual(row['drivetrain'], 'FWD')
        finally:
            store.db.close()

    def test_observation_hash_and_manual_request(self):
        batch = {'observations': [{'vin': VIN, 'asking_price': 24000, 'observed_at': '2026-09-18'}]}
        self.store.import_batch(batch)
        self.store.import_batch(batch)
        self.assertEqual(len(self.store.state()['observations']), 1)
        result = self.store.request({'scope': 'Approved dealer refresh'})
        self.assertEqual(result['status'], 'queued_manual')

    def test_http_origin_and_path_guards(self):
        static = Path(self.temp.name) / 'static'
        static.mkdir()
        (static / 'qa-static.json').write_text(json.dumps({'ok': True}))
        server = service.ThreadingHTTPServer(('127.0.0.1', 0), service.Handler)
        server.store = self.store
        server.static_dir = static
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
            connection.request('GET', '/api/state')
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())['vehicles'], [])
            # A static JSON file is already bytes, and must not be JSON-encoded again.
            connection.request('GET', '/qa-static.json')
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read()), {'ok': True})
            connection.request('GET', '/missing.html')
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            message = json.loads(response.read())['error']
            self.assertIn('No dashboard is installed', message)
            self.assertIn('/api/state', message)
            self.assertIn('/api/export?table=vehicles', message)
            connection.request('POST', '/api/research-request', json.dumps({'scope': 'refresh'}),
                               {'Content-Type': 'application/json', 'Origin': 'https://external.example'})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.request('GET', '/../test.sqlite')
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.request('GET', '/api/state', headers={'Host': 'external.example'})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, content, name='config.json'):
        file = self.dir / name
        file.write_text(content if isinstance(content, str) else json.dumps(content))
        return file

    def test_invalid_config_is_rejected(self):
        good_weights, good_fields = {'a': 1}, ['title']
        bad = {
            'negative weight': dict(weights={'a': -1}, critical_fields=good_fields),
            'zero weight': dict(weights={'a': 0}, critical_fields=good_fields),
            'bool weight': dict(weights={'a': True}, critical_fields=good_fields),
            'string weight': dict(weights={'a': '5'}, critical_fields=good_fields),
            'empty weights': dict(weights={}, critical_fields=good_fields),
            'list weights': dict(weights=[1, 2], critical_fields=good_fields),
            'missing weights': dict(critical_fields=good_fields),
            'string critical_fields': dict(weights=good_weights, critical_fields='title'),
            'object critical_fields': dict(weights=good_weights, critical_fields={'title': True}),
            'empty-string field': dict(weights=good_weights, critical_fields=['title', '']),
            'non-string field': dict(weights=good_weights, critical_fields=['title', 1]),
            'missing critical_fields': dict(weights=good_weights),
            'not an object': ['weights'],
        }
        for label, config in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    service.load_config(self.write(config))
                with self.assertRaises(ValueError):
                    service.Store(self.dir / 'never.sqlite', config)
        with self.subTest('not json'):
            with self.assertRaises(ValueError):
                service.load_config(self.write('{not json'))
        with self.subTest('infinite weight'):
            with self.assertRaises(ValueError):
                service.load_config(self.write('{"weights": {"a": Infinity}, "critical_fields": []}'))

    def test_valid_custom_config_loads(self):
        config = dict(weights={'a': 20, 'b': 30.5}, critical_fields=['color'])
        self.assertEqual(service.load_config(self.write(config)), config)
        self.assertEqual(service.load_config(self.write(dict(weights={'a': 1}, critical_fields=[]))),
                         dict(weights={'a': 1}, critical_fields=[]))

    def test_missing_config_falls_back_to_defaults(self):
        config = service.load_config(self.dir / 'absent.json')
        self.assertEqual(config, service.DEFAULT_CONFIG)
        config['weights']['history'] = 1
        config['critical_fields'].append('x')
        self.assertEqual(service.DEFAULT_CONFIG['weights']['history'], 18)
        self.assertNotIn('x', service.DEFAULT_CONFIG['critical_fields'])

    def test_explicit_missing_config_is_an_error(self):
        with self.assertRaises(ValueError):
            service.load_config(self.dir / 'absent.json', required=True)
        database = self.dir / 'never.sqlite'
        result = subprocess.run([sys.executable, str(path), '--config', str(self.dir / 'typo.json'),
                                 '--db', str(database), '--port', '0'],
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('typo.json', result.stderr)
        self.assertFalse(database.exists())

    def test_scores_outside_current_rubric_are_flagged_not_fatal(self):
        database = self.dir / 'shared.sqlite'
        before = service.Store(database)
        before.import_batch({'vehicles': [{'vin': VIN, 'scores': {'history': 15, 'fit': 5}},
                                          {'vin': '2HGCM82633A004353', 'scores': {'history': 10}}]})
        before.db.close()
        after = service.Store(database, dict(weights={'history': 12, 'comfort': 7}, critical_fields=[]))
        try:
            stale, fine = after.state()['vehicles']
            self.assertIsNone(stale['score'])
            self.assertIsNone(stale['score_summary'])
            self.assertIn('fit', stale['score_problem'])
            self.assertEqual(stale['scores'], {'history': 15, 'fit': 5})
            self.assertEqual(fine['score']['earned'], 10)
            self.assertNotIn('score_problem', fine)
        finally:
            after.db.close()

    def test_shipped_config_matches_defaults(self):
        self.assertEqual(service.load_config(path.parent / 'config.json'), service.DEFAULT_CONFIG)
        self.assertEqual(sum(service.DEFAULT_CONFIG['weights'].values()), 100)

    def test_server_exits_on_invalid_config_before_starting(self):
        config = self.write(dict(weights={'a': -1}, critical_fields=[]))
        database = self.dir / 'never.sqlite'
        result = subprocess.run([sys.executable, str(path), '--config', str(config), '--db', str(database), '--port', '0'],
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('weight for a must be a positive number', result.stderr)
        self.assertFalse(database.exists())

if __name__ == '__main__':
    unittest.main()

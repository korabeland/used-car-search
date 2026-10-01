#!/usr/bin/env python3
"""Local-only, dependency-free used-car research database and API server."""
import argparse
import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

DEFAULT_CONFIG = dict(
    weights=dict(history=18, service=22, price=15, mileage=10, powertrain=10,
                 ownership=5, condition=10, fit=7, dealer=3),
    critical_fields=['drivetrain', 'title', 'title_status', 'structural_damage', 'flood', 'odometer_conflict'])
TABLES = ('vehicles', 'dealers', 'evidence', 'observations', 'decisions', 'changes', 'research_requests')
VIN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

def now():
    return datetime.now(timezone.utc).isoformat()

def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)

def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('config must be a JSON object')
    weights = config.get('weights')
    if not isinstance(weights, dict) or not weights:
        raise ValueError('weights must be a non-empty object')
    for key, points in weights.items():
        if (isinstance(points, bool) or not isinstance(points, (int, float))
                or (isinstance(points, float) and not math.isfinite(points)) or points <= 0):
            raise ValueError('weight for ' + key + ' must be a positive number')
    fields = config.get('critical_fields')
    if not isinstance(fields, list) or not all(isinstance(field, str) and field for field in fields):
        raise ValueError('critical_fields must be a list of non-empty strings')
    return dict(weights=dict(weights), critical_fields=list(fields))

def load_config(path, required=False):
    try:
        text = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        if required:
            raise ValueError(f'Config file not found: {path}')
        return validate_config(DEFAULT_CONFIG)
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f'Cannot read config {path}: {error}')
    try:
        return validate_config(json.loads(text))
    except ValueError as error:
        raise ValueError(f'Invalid config {path}: {error}')

def score(value, weights=None):
    weights = DEFAULT_CONFIG['weights'] if weights is None else weights
    if not isinstance(value, dict) or set(value) - set(weights):
        raise ValueError('scores must be an object using the published rubric keys')
    for key, points in value.items():
        if points is not None and (isinstance(points, bool) or not isinstance(points, (int, float))
                                   or not 0 <= points <= weights[key]):
            raise ValueError('Invalid score for ' + key)
    total = sum(weights.values())
    earned = sum(points for points in value.values() if points is not None)
    checkable = sum(weights[key] for key, points in value.items() if points is not None)
    return dict(earned=earned, checkable=checkable, coverage=round(100 * checkable / total),
                max=earned + total - checkable)

class Store:
    def __init__(self, path, config=None):
        config = validate_config(DEFAULT_CONFIG if config is None else config)
        self.weights = config['weights']
        self.critical_fields = config['critical_fields']
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        for table in TABLES:
            self.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.commit()

    def rows(self, table):
        return [json.loads(row[0]) for row in self.db.execute(f'SELECT data FROM {table} ORDER BY rowid')]

    def put(self, table, key, row):
        self.db.execute(f'INSERT OR REPLACE INTO {table} VALUES (?, ?)', (key, encoded(row)))

    def event(self, entity, kind, detail):
        stamp = now()
        row = dict(id=hashlib.sha256((stamp + entity + kind).encode()).hexdigest(),
                   entity_id=entity, kind=kind, detail=detail, timestamp=stamp)
        self.put('changes', row['id'], row)

    def state(self):
        with self.lock:
            result = {table: self.rows(table) for table in TABLES}
            for vehicle in result['vehicles']:
                try:
                    vehicle['score'] = score(vehicle.get('scores', {}), self.weights)
                except ValueError:
                    # Stored scores predate a config change; withhold the summary rather than guess.
                    unknown = sorted(set(vehicle.get('scores', {})) - set(self.weights))
                    vehicle['score'] = vehicle['score_summary'] = None
                    vehicle['score_problem'] = ('Stored scores do not fit the current rubric'
                                                + (' (unknown categories: ' + ', '.join(unknown) + ')' if unknown else '')
                                                + '; re-score this vehicle.')
                    continue
                vehicle['score_summary'] = {**vehicle['score'], 'maximum': vehicle['score']['max']}
            stamps = [row.get('timestamp', '') for row in result['changes']]
            result.update(updated_at=max(stamps, default=None), rubric=dict(self.weights))
            return result

    def import_batch(self, batch):
        if not isinstance(batch, dict) or set(batch) - set(TABLES[:4]):
            raise ValueError('Import accepts vehicles, dealers, evidence, observations only')
        prepared = []
        for table, rows in batch.items():
            if not isinstance(rows, list):
                raise ValueError(table + ' must be an array')
            for source in rows:
                if not isinstance(source, dict):
                    raise ValueError('Each record must be an object')
                row = dict(source)
                if table == 'vehicles':
                    if not isinstance(row.get('vin'), str) or not VIN.fullmatch(row['vin']):
                        raise ValueError('Every vehicle requires a valid 17-character VIN')
                    if 'scores' in row:
                        score(row['scores'], self.weights)
                    key = row['vin']
                    row.pop('score', None)
                    row.pop('score_summary', None)
                    row.pop('conflicts', None)
                else:
                    if 'vin' in row and (not isinstance(row['vin'], str) or not VIN.fullmatch(row['vin'])):
                        raise ValueError('Invalid record VIN')
                    if table == 'observations' and not row.get('id'):
                        row['id'] = hashlib.sha256(encoded(row).encode()).hexdigest()
                    key = row.get('id')
                    if not isinstance(key, str) or not key.strip():
                        raise ValueError(table + ' requires a nonempty string id')
                encoded(row)
                prepared.append((table, key, row))
        count = 0
        with self.lock, self.db:
            for table, key, row in prepared:
                previous = self.db.execute(f'SELECT data FROM {table} WHERE id=?', (key,)).fetchone()
                old = json.loads(previous[0]) if previous else {}
                merged = {**old, **row}
                if table == 'vehicles':
                    if 'scores' in row:
                        merged['scores'] = {**old.get('scores', {}), **row['scores']}
                    conflicts = list(old.get('conflicts', []))
                    for field in self.critical_fields:
                        if field in row and old.get(field) is not None and row[field] is not None and old[field] != row[field]:
                            conflict = dict(field=field, previous=old[field], incoming=row[field])
                            if conflict not in conflicts:
                                conflicts.append(conflict)
                            merged[field] = old[field]
                    if conflicts:
                        merged['conflicts'] = conflicts
                        merged['review_status'] = 'Needs conflict review'
                if merged != old:
                    self.put(table, key, merged)
                    differences = {field: {'previous': old.get(field), 'current': merged.get(field)}
                                   for field in set(old) | set(merged) if old.get(field) != merged.get(field)}
                    self.event(key, 'updated' if previous else 'added',
                               dict(table=table, fields=sorted(differences), differences=differences))
                    count += 1
        return dict(changed=count)

    def decision(self, body):
        if not isinstance(body, dict) or not all(isinstance(body.get(k), str) and body[k].strip()
                                              for k in ('entity_id', 'decision', 'gate')):
            raise ValueError('Decision requires entity_id, decision, and gate strings')
        if not isinstance(body.get('note', ''), str):
            raise ValueError('note must be a string')
        row = {key: body.get(key, '') for key in ('entity_id', 'decision', 'gate', 'note')}
        row['timestamp'] = now()
        row['id'] = hashlib.sha256(encoded(row).encode()).hexdigest()
        with self.lock, self.db:
            self.put('decisions', row['id'], row)
            self.event(row['entity_id'], 'decision', row)
        return row

    def request(self, body):
        if not isinstance(body, dict) or not isinstance(body.get('scope'), str) or not body['scope'].strip():
            raise ValueError('A research scope string is required')
        row = dict(scope=body['scope'], timestamp=now(), status='queued_manual')
        row['prompt'] = ('Refresh car research for: ' + body['scope'] + '. Read the saved workflow and current database; '
                         'respect approved gates, research changed evidence only, retain source links and timestamps, '
                         'and import verified findings. This saved request has not started any agents.')
        row['id'] = hashlib.sha256(encoded(row).encode()).hexdigest()
        with self.lock, self.db:
            self.put('research_requests', row['id'], row)
            self.event(row['id'], 'research_requested', dict(scope=row['scope']))
        return row

class Handler(BaseHTTPRequestHandler):
    def reply(self, value, status=200, content_type='application/json; charset=utf-8'):
        data = value if isinstance(value, bytes) else encoded(value).encode() if content_type.startswith('application/json') else value
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def local_request(self, mutate=False):
        host = self.headers.get('Host', '')
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if host not in allowed:
            self.reply({'error': 'Only the local dashboard host is allowed'}, 403)
            return False
        origin = self.headers.get('Origin')
        if (origin and origin != 'http://' + host) or (mutate and self.headers.get('Sec-Fetch-Site') == 'cross-site'):
            self.reply({'error': 'Same-origin requests only'}, 403)
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        url = urlparse(self.path)
        if url.path == '/api/state':
            return self.reply(self.server.store.state())
        if url.path == '/api/export':
            table = parse_qs(url.query).get('table', [''])[0]
            if table not in ('vehicles', 'dealers', 'evidence', 'decisions', 'changes'):
                return self.reply({'error': 'Invalid export table'}, 400)
            rows = self.server.store.state()[table]
            columns = sorted({key for row in rows for key in row}) or ['vin' if table == 'vehicles' else 'id']
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                clean = {}
                for key, value in row.items():
                    value = encoded(value) if isinstance(value, (dict, list)) else value
                    if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')):
                        value = "'" + value
                    clean[key] = value
                writer.writerow(clean)
            return self.reply(stream.getvalue().encode(), content_type='text/csv; charset=utf-8')
        if url.path.startswith('/api/'):
            return self.reply({'error': 'Unknown endpoint'}, 404)
        base = self.server.static_dir.resolve()
        target = (base / unquote(url.path).lstrip('/')).resolve()
        if not target.is_relative_to(base):
            return self.reply({'error': 'Invalid path'}, 403)
        if target.is_dir():
            target = target / 'index.html'
        if not target.is_file():
            return self.reply({'error': 'No dashboard is installed; use /api/state or /api/export?table=vehicles for the data'}, 404)
        import mimetypes
        return self.reply(target.read_bytes(), content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')

    def do_POST(self):
        if not self.local_request(mutate=True):
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply({'error': 'application/json required'}, 415)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 5 * 1024 * 1024:
                return self.reply({'error': 'Body must be between 1 byte and 5 MiB'}, 413)
            body = json.loads(self.rfile.read(length), parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite number')))
            route = urlparse(self.path).path
            actions = {'/api/import': self.server.store.import_batch, '/api/decision': self.server.store.decision,
                       '/api/research-request': self.server.store.request}
            if route not in actions:
                return self.reply({'error': 'Unknown endpoint'}, 404)
            self.reply(actions[route](body))
        except (ValueError, TypeError, UnicodeDecodeError) as error:
            self.reply({'error': str(error)}, 400)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parent
    parser.add_argument('--port', type=int, default=4173)
    parser.add_argument('--db', type=Path, default=root / 'search.sqlite')
    parser.add_argument('--static-dir', type=Path, default=root.parent / 'dashboard')
    parser.add_argument('--config', type=Path, default=None)
    args = parser.parse_args()
    try:
        config = load_config(args.config or root / 'config.json', required=args.config is not None)
    except ValueError as error:
        raise SystemExit('Error: ' + str(error))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.store = Store(args.db, config)
    server.static_dir = args.static_dir
    print(f'Used-car search service: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.store.db.close()

if __name__ == '__main__':
    main()

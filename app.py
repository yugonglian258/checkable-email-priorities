"""Serve the checkable email-priority prototype on localhost using Python 3.10+."""
import argparse
import json
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import uuid4

import triage

HERE = Path(__file__).resolve().parent
DATA = triage.load_inputs()
THREADS = {thread['id']: {key: value for key, value in thread.items() if key != 'expected'}
           for case in DATA['cases'].values() for thread in case['threads']}
SESSIONS = {}


def state(session, version='v2'):
    if version not in ('v1', 'v2'):
        raise ValueError('Unknown demonstration version')
    now = triage.datetime.fromisoformat(DATA['now'])
    return {'clock': DATA['now'], 'version': version,
            'threads': [dict(THREADS[key], result=triage.classify(THREADS[key], now, version))
                        for key in THREADS],
            'labels': session.labels, 'can_undo': bool(session.history)}


def act(session, request):
    version = request.get('version', 'v2')
    if version not in ('v1', 'v2'):
        raise ValueError('Unknown demonstration version')
    action = request.get('action')
    if action == 'refresh':
        return dict(state(session, version), feedback={'message': 'Suggestion engine changed. Review the new suggestion.'})
    if action == 'undo':
        feedback = session.undo()
    elif action == 'choose':
        thread = THREADS.get(request.get('thread'))
        if thread is None:
            raise ValueError('Unknown thread')
        result = triage.classify(thread, triage.datetime.fromisoformat(DATA['now']), version)
        feedback = session.choose(result, request.get('choice'))
    else:
        raise ValueError('Unknown action')
    return dict(state(session, version), feedback=feedback)


class Handler(BaseHTTPRequestHandler):
    def session(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get('Cookie', ''))
        key = cookie['demo'].value if 'demo' in cookie else None
        if key not in SESSIONS:
            key = uuid4().hex
            SESSIONS[key] = triage.LabelSession()
        self.session_key = key
        return SESSIONS[key]

    def send(self, status, body, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if hasattr(self, 'session_key'):
            self.send_header('Set-Cookie', 'demo=' + self.session_key + '; HttpOnly; SameSite=Strict; Path=/')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send(200, (HERE / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        elif self.path == '/api/state':
            self.send(200, json.dumps(state(self.session())).encode())
        else:
            self.send(404, b'{"error":"Not found"}')

    def do_POST(self):
        if self.path != '/api/action':
            return self.send(404, b'{"error":"Not found"}')
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= 4096:
                raise ValueError('Invalid request size')
            request = json.loads(self.rfile.read(size))
            if not isinstance(request, dict):
                raise ValueError('Request must be an object')
            data = act(self.session(), request)
        except (ValueError, TypeError, KeyError) as error:
            return self.send(400, json.dumps({'error': str(error)}).encode())
        self.send(200, json.dumps(data).encode())

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8012)
    args = parser.parse_args()
    print(f'Open http://localhost:{args.port}', flush=True)
    HTTPServer(('localhost', args.port), Handler).serve_forever()

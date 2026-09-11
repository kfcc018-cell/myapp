from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from uuid import uuid4
import json
import random
import time
import base64
import binascii

from database import DatabaseError, get_bosses, get_rankings, save_result
from admin_upload import create_item

ROOT = Path(__file__).resolve().parent
GAMES = {}
LOCK = Lock()


def snapshot(game):
    size = len(game['current'])
    pair = game['current'][game['match'] * 2:game['match'] * 2 + 2]
    return {'game_id': game['id'], 'pair': pair, 'size': size,
            'match': game['match'], 'total': game['total'],
            'champion': game['champion'], 'saved': game['saved']}


class Handler(BaseHTTPRequestHandler):
    def reply(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path in ('/', '/index.html', '/app.js', '/stats.css', '/cards.css', '/admin.html', '/admin.js', '/statistics.html', '/statistics.js'):
            filename = path.lstrip('/') or 'index.html'
            body = (ROOT / filename).read_bytes()
            self.send_response(200)
            content_type = 'text/css' if path.endswith('.css') else 'text/javascript' if path.endswith('.js') else 'text/html'
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == '/api/rankings':
            try:
                self.reply(get_rankings())
            except DatabaseError as exc:
                self.reply({'error': str(exc)}, 503)
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            limit = 7 * 1024 * 1024 if self.path == '/api/items' else 4096
            if not 0 < length <= limit:
                raise ValueError('잘못된 요청입니다.')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('잘못된 요청입니다.')
            if self.path == '/api/items':
                try:
                    content = data.get('content', '')
                    if not isinstance(content, str):
                        raise ValueError('항목 설명을 입력해주세요.')
                    photo = base64.b64decode(data.get('photo', ''), validate=True)
                    create_item(content, photo)
                except (ValueError, binascii.Error) as exc:
                    self.reply({'error': str(exc)}, 400)
                    return
                self.reply({'success': True}, 201)
                return
            with LOCK:
                if self.path == '/api/game':
                    now = time.monotonic()
                    for key in list(GAMES):
                        if now - GAMES[key]['created'] > 86400:
                            del GAMES[key]
                    if len(GAMES) >= 1000:
                        self.reply({'error': '잠시 후 다시 시도해주세요.'}, 503)
                        return
                    candidates = get_bosses()
                    candidates = random.sample(candidates, min(8, len(candidates)))
                    game = {'id': str(uuid4()), 'current': random.sample(candidates, len(candidates)),
                            'winners': [], 'match': 0, 'total': len(candidates),
                            'champion': None, 'saved': False, 'created': now}
                    GAMES[game['id']] = game
                    self.reply(snapshot(game))
                elif self.path in ('/api/choose', '/api/result'):
                    game = GAMES.get(str(data.get('game_id', '')))
                    if not game:
                        self.reply({'error': '게임이 만료됐습니다. 새 게임을 시작해주세요.'}, 410)
                        return
                    if self.path == '/api/choose':
                        if game['champion']:
                            self.reply(snapshot(game))
                            return
                        pair = game['current'][game['match'] * 2:game['match'] * 2 + 2]
                        # Stale/double requests return current state without recording another choice.
                        if data.get('size') != len(game['current']) or data.get('match') != game['match']:
                            self.reply(snapshot(game))
                            return
                        boss = next((b for b in pair if b['id'] == data.get('winner_id')), None)
                        if not boss:
                            raise ValueError('현재 대진의 후보를 선택해주세요.')
                        game['winners'].append(boss)
                        game['match'] += 1
                        if game['match'] == len(game['current']) // 2:
                            if len(game['current']) % 2:
                                game['winners'].append(game['current'][-1])
                            if len(game['winners']) == 1:
                                game['champion'] = game['winners'][0]
                            else:
                                game['current'], game['winners'], game['match'] = game['winners'], [], 0
                        self.reply(snapshot(game))
                    else:
                        if not game['champion']:
                            raise ValueError('게임을 먼저 완료해주세요.')
                        if not game['saved']:
                            save_result(game['id'], game['champion']['id'])
                            game['saved'] = True
                        self.reply({'saved': True})
                else:
                    self.send_error(404)
        except (ValueError, TypeError, UnicodeError):
            self.reply({'error': '요청이 올바르지 않습니다.'}, 400)
        except DatabaseError as exc:
            self.reply({'error': str(exc)}, 503)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8000), Handler)
    print('최악의 직장상사 월드컵: http://127.0.0.1:8000', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

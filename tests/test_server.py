import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from server import Handler, ThreadingHTTPServer, GAMES


class ServerTests(unittest.TestCase):
    def test_game_validation_and_save_once(self):
        bosses = [{'id': i, 'name': str(i), 'emoji': 'X'} for i in range(32)]
        with patch('server.get_bosses', return_value=bosses), patch('server.save_result') as save:
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            def post(path, data):
                req = Request(base + path, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
                with urlopen(req) as r:
                    return json.load(r)
            try:
                game = post('/api/game', {})
                self.assertEqual(game['total'], 8)
                with self.assertRaises(HTTPError) as error:
                    post('/api/result', {'game_id': game['game_id']})
                self.assertEqual(error.exception.code, 400)
                payload = {'game_id': game['game_id'], 'size': game['size'], 'match': game['match'], 'winner_id': game['pair'][0]['id']}
                game = post('/api/choose', payload)
                stale = post('/api/choose', payload)
                self.assertEqual(game, stale)
                for _ in range(6):
                    game = post('/api/choose', {'game_id': game['game_id'], 'size': game['size'], 'match': game['match'], 'winner_id': game['pair'][0]['id']})
                self.assertIsNotNone(game['champion'])
                post('/api/result', {'game_id': game['game_id']})
                post('/api/result', {'game_id': game['game_id']})
                save.assert_called_once_with(game['game_id'], game['champion']['id'])
                with urlopen(base + '/app.js') as r:
                    self.assertEqual(r.status, 200)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                GAMES.clear()


if __name__ == '__main__':
    unittest.main()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from uuid import uuid4
from streamlit.testing.v1 import AppTest
import database

BOSSES = [{'id': i, 'name': f'Boss {i}', 'emoji': 'X', 'description': ''} for i in range(1, 33)]
RANKINGS = [{'winner_id': 1, 'content': 'Boss 1', 'win_count': 1, 'win_percentage': 100}]


class IntegrationTests(unittest.TestCase):
    def test_tournament_save_refresh_restart(self):
        with patch('database.get_bosses', return_value=BOSSES), patch('database.save_result') as save, patch('database.get_rankings', return_value=RANKINGS):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')).run()
            game_id = app.session_state['game_id']
            self.assertEqual(len(app.session_state['current']), 8)
            self.assertEqual(len({b['id'] for b in app.session_state['current']}), 8)
            for _ in range(7):
                app.button[0].click().run()
                self.assertFalse(app.exception)
            self.assertTrue(app.session_state['saved'])
            save.assert_called_once_with(game_id, app.session_state['champion']['id'])
            self.assertTrue(any('ranking-chart' in m.value for m in app.markdown))
            app.button[0].click().run()
            save.assert_called_once()
            app.button[1].click().run()
            self.assertNotEqual(app.session_state['game_id'], game_id)
            self.assertIsNone(app.session_state['champion'])

    def test_failed_save_retry_uses_same_game_id(self):
        with patch('database.get_bosses', return_value=BOSSES[:2]), patch('database.save_result', side_effect=[database.DatabaseError('retry'), None]) as save, patch('database.get_rankings', return_value=RANKINGS):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')).run()
            app.button[0].click().run()
            self.assertFalse(app.session_state['saved'])
            app.button[0].click().run()
            self.assertTrue(app.session_state['saved'])
            self.assertEqual(save.call_args_list[0], save.call_args_list[1])

    def test_odd_candidates_and_load_failure(self):
        with patch('database.get_bosses', return_value=BOSSES[:5]), patch('database.save_result'), patch('database.get_rankings', return_value=RANKINGS):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')).run()
            for _ in range(4):
                app.button[0].click().run()
            self.assertTrue(app.session_state['saved'])
            self.assertFalse(app.exception)
        with patch('database.get_bosses', side_effect=database.DatabaseError('offline')):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.error), 1)

    def test_duplicate_result_and_conflicting_winner(self):
        conflict = HTTPError('https://example.test', 409, 'Conflict', {}, None)
        with patch('database.request', side_effect=[conflict, [{'winner_id': 1}]]):
            database.save_result(str(uuid4()), 1)
        with patch('database.request', side_effect=[conflict, [{'winner_id': 2}]]):
            with self.assertRaises(database.DatabaseError):
                database.save_result(str(uuid4()), 1)


if __name__ == '__main__':
    unittest.main()

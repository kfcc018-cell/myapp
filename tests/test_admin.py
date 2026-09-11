import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import io
import unittest
from unittest.mock import patch
from PIL import Image
from admin_upload import create_item, prepare_image
from streamlit.testing.v1 import AppTest

class AdminTests(unittest.TestCase):
    def test_missing_bucket_400_creates_bucket(self):
        from urllib.error import HTTPError
        data = io.BytesIO()
        Image.new('RGB', (10, 10)).save(data, format='PNG')
        missing = HTTPError('https://test', 400, 'Bad Request', {}, io.BytesIO(b'{"code":"NoSuchBucket","message":"Bucket not found"}'))
        with patch('admin_upload.storage', side_effect=[missing, b'{}', b'{}']) as files, patch('admin_upload.settings', return_value=('https://test.supabase.co', 'secret')), patch('admin_upload.request') as db:
            create_item('New item', data.getvalue())
            self.assertEqual(files.call_args_list[1].args[:2], ('bucket', 'POST'))
            db.assert_called_once()

    def test_permission_error_does_not_create_bucket(self):
        from urllib.error import HTTPError
        from database import DatabaseError
        data = io.BytesIO()
        Image.new('RGB', (10, 10)).save(data, format='PNG')
        denied = HTTPError('https://test', 403, 'Forbidden', {}, io.BytesIO(b'{}'))
        with patch('admin_upload.storage', side_effect=denied) as files, patch('admin_upload.request') as db:
            with self.assertRaises(DatabaseError):
                create_item('New item', data.getvalue())
            files.assert_called_once()
            db.assert_not_called()

    def test_edit_without_photo_and_soft_delete(self):
        from admin_upload import delete_item
        with patch('admin_upload.request', return_value=[{'id': 1}]) as db, patch('admin_upload.storage') as files:
            create_item('Changed', None, 1)
            self.assertEqual(db.call_args.kwargs['method'], 'PATCH')
            self.assertEqual(db.call_args.args[1], {'content': 'Changed'})
            files.assert_not_called()
            delete_item(1)
            self.assertIn('deleted_at', db.call_args.args[1])
            self.assertEqual(db.call_args.kwargs['method'], 'PATCH')

    def test_statistics_without_starting_game(self):
        with patch('database.get_rankings', return_value=[]), patch('database.get_bosses') as candidates, patch('database.save_result') as save:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py'))
            app.session_state['stats_open'] = True
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any('ranking-chart' in m.value for m in app.markdown))
            candidates.assert_not_called()
            save.assert_not_called()

    def test_upload_and_insert(self):
        data = io.BytesIO()
        Image.new('RGB', (10, 10)).save(data, format='PNG')
        with patch('admin_upload.storage') as storage, patch('admin_upload.settings', return_value=('https://test.supabase.co', 'secret')), patch('admin_upload.request') as db:
            create_item(' Test boss ', data.getvalue())
            self.assertEqual(storage.call_count, 2)
            row = db.call_args.args[1]
            self.assertEqual(row['content'], 'Test boss')
            self.assertIn('/storage/v1/object/public/boss-worldcup-images/', row['img_filename'])
            self.assertTrue(row['img_filename'].endswith('.jpg'))
        with self.assertRaises(ValueError):
            prepare_image(b'not an image')
        with self.assertRaises(ValueError):
            prepare_image(b'x' * (5 * 1024 * 1024 + 1))

    def test_admin_opens_without_database_key(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py'))
        app.session_state['admin_open'] = True
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, '항목 관리')
        self.assertEqual(len(app.text_input), 1)

if __name__ == '__main__':
    unittest.main()

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

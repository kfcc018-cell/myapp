"""Server-side Supabase access. Never expose the secret key to the browser."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from uuid import UUID

DEFAULT_URL = 'https://uvkdwnedqxgczeterdef.supabase.co'


class DatabaseError(Exception):
    pass


def settings():
    url = os.environ.get('SUPABASE_URL', DEFAULT_URL)
    key = os.environ.get('SUPABASE_SECRET_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not key:
        try:
            import streamlit as st
            url = st.secrets.get('SUPABASE_URL', url)
            key = st.secrets.get('SUPABASE_SECRET_KEY') or st.secrets.get('SUPABASE_SERVICE_ROLE_KEY')
        except (ImportError, FileNotFoundError):
            pass
    if not key:
        raise DatabaseError('서버 설정이 필요합니다. Streamlit Secrets에 SUPABASE_SECRET_KEY를 등록해주세요.')
    return url.rstrip('/'), key


def request(path, data=None):
    url, key = settings()
    headers = {'apikey': key, 'Content-Type': 'application/json'}
    if key.startswith('eyJ'):
        headers['Authorization'] = 'Bearer ' + key
    if data is not None:
        headers['Prefer'] = 'return=minimal'
    req = Request(url + '/rest/v1/' + path, headers=headers,
                  data=json.dumps(data).encode() if data is not None else None)
    try:
        with urlopen(req, timeout=15) as response:
            body = response.read()
            return json.loads(body) if body else None
    except HTTPError:
        raise
    except (URLError, TimeoutError, ValueError) as exc:
        raise DatabaseError('데이터베이스에 연결하지 못했습니다. 다시 시도해주세요.') from exc


def image_url(value):
    value = str(value or '').strip()
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ('https', 'http') and parsed.hostname else ''
    except ValueError:
        return ''


def get_bosses():
    try:
        rows = request('boss_worldcup_items?select=id,content,img_filename&order=id')
    except HTTPError as exc:
        raise DatabaseError('후보를 불러오지 못했습니다. 서버 연결 설정을 확인해주세요.') from exc
    if len(rows) < 2:
        raise DatabaseError('후보가 2개 이상 필요합니다.')
    return [{'id': row['id'], 'name': row['content'], 'image_url': image_url(row.get('img_filename')),
             'emoji': '👔', 'description': ''} for row in rows]


def save_result(game_id, winner_id):
    game_id = str(UUID(str(game_id)))
    if type(winner_id) is not int or winner_id <= 0:
        raise ValueError('올바르지 않은 후보입니다.')
    try:
        request('boss_worldcup_results', {'game_id': game_id, 'winner_id': winner_id})
    except HTTPError as exc:
        if exc.code == 409:
            try:
                rows = request(f'boss_worldcup_results?game_id=eq.{game_id}&select=winner_id')
                if rows and rows[0]['winner_id'] == winner_id:
                    return
            except HTTPError:
                pass
        raise DatabaseError('결과를 저장하지 못했습니다. 다시 시도해주세요.') from exc


def get_rankings():
    try:
        return request('boss_worldcup_rankings?select=winner_id,content,win_count,win_percentage&order=win_count.desc,winner_id.asc')
    except HTTPError as exc:
        raise DatabaseError('통계를 불러오지 못했습니다.') from exc

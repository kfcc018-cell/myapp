"""Server-side image registration; database keys never reach the browser."""
import io
import json
import warnings
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from PIL import Image, ImageOps, UnidentifiedImageError
from database import DatabaseError, request, settings
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote

BUCKET = 'boss-worldcup-images'
MAX_BYTES = 5 * 1024 * 1024


def storage_error(exc):
    if not hasattr(exc, 'storage_detail'):
        try:
            detail = json.loads(exc.read())
            exc.storage_detail = detail if isinstance(detail, dict) else {}
        except (ValueError, OSError):
            exc.storage_detail = {}
    return exc.storage_detail


def missing_bucket(exc):
    detail = storage_error(exc)
    return exc.code == 404 or (exc.code == 400 and (
        detail.get('code') == 'NoSuchBucket' or
        detail.get('message') == 'Bucket not found' or detail.get('error') == 'Bucket not found'))


def prepare_image(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('사진은 5MB 이하로 선택해주세요.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 20_000_000:
                    raise ValueError('JPG, PNG, WEBP 사진(2천만 화소 이하)을 선택해주세요.')
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((1600, 1600))
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=85)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('정상적인 이미지 파일을 선택해주세요.') from exc


def storage(path, method='GET', body=None, content_type='application/json'):
    url, key = settings()
    headers = {'apikey': key, 'Content-Type': content_type}
    if key.startswith('eyJ'):
        headers['Authorization'] = 'Bearer ' + key
    req = Request(url + '/storage/v1/' + path, data=body, method=method, headers=headers)
    with urlopen(req, timeout=30) as response:
        return response.read()


def create_item(content, raw, item_id=None):
    content = content.strip()
    if not 1 <= len(content) <= 200:
        raise ValueError('항목 설명은 1~200자로 입력해주세요.')
    if item_id is not None:
        item_id = valid_id(item_id)
        try:
            if not request(f'boss_worldcup_items?id=eq.{item_id}&deleted_at=is.null&select=id'):
                raise ValueError('항목을 찾을 수 없습니다. 목록을 새로고침해주세요.')
        except HTTPError as exc:
            raise DatabaseError('항목을 조회하지 못했습니다.') from exc
    if raw is None and item_id is not None:
        try:
            request(f'boss_worldcup_items?id=eq.{item_id}&deleted_at=is.null', {'content': content}, method='PATCH')
            return
        except HTTPError as exc:
            raise DatabaseError('수정하지 못했습니다.') from exc
    photo = prepare_image(raw)
    filename = str(uuid4()) + '.jpg'
    stage = '사진 저장소 확인'
    try:
        try:
            storage('bucket/' + BUCKET)
        except HTTPError as exc:
            if not missing_bucket(exc):
                raise
            stage = '사진 저장소 생성'
            try:
                storage('bucket', 'POST', json.dumps({'id': BUCKET, 'name': BUCKET, 'public': True,
                        'file_size_limit': MAX_BYTES, 'allowed_mime_types': ['image/jpeg']}).encode())
            except HTTPError as conflict:
                detail = storage_error(conflict)
                if conflict.code != 409 and detail.get('code') not in ('BucketAlreadyExists', 'ResourceAlreadyExists') and detail.get('message') != 'The resource already exists':
                    raise
                storage('bucket/' + BUCKET)
        stage = '사진 업로드'
        storage('object/' + BUCKET + '/' + filename, 'POST', photo, 'image/jpeg')
        url, _ = settings()
        payload = {'content': content, 'img_filename': url + '/storage/v1/object/public/' + BUCKET + '/' + filename}
        stage = '항목 저장'
        if item_id is None:
            request('boss_worldcup_items', payload)
        else:
            request(f'boss_worldcup_items?id=eq.{item_id}&deleted_at=is.null', payload, method='PATCH')
    except HTTPError as exc:
        hint = ' 서버용 Supabase 키와 권한을 확인해주세요.' if exc.code in (401, 403) else ' 다시 시도해주세요.'
        raise DatabaseError(f'{stage} 실패 (HTTP {exc.code}).{hint}') from exc
    except (URLError, TimeoutError) as exc:
        raise DatabaseError(f'{stage} 중 연결이 끊겼습니다. 다시 시도해주세요.') from exc


def valid_id(item_id):
    if type(item_id) is not int or item_id <= 0:
        raise ValueError('올바르지 않은 항목입니다.')
    return item_id


def list_items():
    try:
        rows = request('boss_worldcup_items?select=id,content,img_filename&deleted_at=is.null&order=id.desc')
        for row in rows:
            row['filename'] = unquote(urlsplit(row['img_filename']).path.rsplit('/', 1)[-1])
        return rows
    except HTTPError as exc:
        raise DatabaseError('목록을 불러오지 못했습니다.') from exc


def delete_item(item_id):
    item_id = valid_id(item_id)
    try:
        request(f'boss_worldcup_items?id=eq.{item_id}&deleted_at=is.null',
                {'deleted_at': datetime.now(timezone.utc).isoformat()}, method='PATCH')
    except HTTPError as exc:
        raise DatabaseError('삭제하지 못했습니다.') from exc

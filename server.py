from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
BOSSES = [
    {"id": 1, "emoji": "🏆", "name": "공 가로채는 상사", "description": "일은 내가 했는데, 보고할 땐 전부 자기 성과."},
    {"id": 2, "emoji": "📱", "name": "퇴근 후 연락하는 상사", "description": "밤 11시에도 '잠깐 통화 가능하지?'"},
    {"id": 3, "emoji": "🌪️", "name": "말 바꾸는 상사", "description": "어제는 A라더니 오늘은 '왜 B로 안 했어?'"},
    {"id": 4, "emoji": "📢", "name": "공개 망신 주는 상사", "description": "작은 실수도 모두가 보는 자리에서 크게 지적."},
    {"id": 5, "emoji": "👀", "name": "감시하는 상사", "description": "자리 비운 5분도 어디 다녀왔는지 확인."},
    {"id": 6, "emoji": "🫥", "name": "책임 떠넘기는 상사", "description": "문제가 생기면 '그건 담당자가 한 일이죠.'"},
    {"id": 7, "emoji": "🍻", "name": "회식 강요하는 상사", "description": "자율 참석이라면서 불참하면 다음 날 면담."},
    {"id": 8, "emoji": "⏰", "name": "퇴근 직전 일 주는 상사", "description": "하루 종일 조용하다가 5시 59분에 '오늘까지.'"},
]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/bosses':
            body = json.dumps(BOSSES, ensure_ascii=False).encode('utf-8')
            content_type = 'application/json; charset=utf-8'
        elif path in ('/', '/index.html'):
            body = (ROOT / 'index.html').read_bytes()
            content_type = 'text/html; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    address = ('127.0.0.1', 8000)
    server = ThreadingHTTPServer(address, Handler)
    print('최악의 직장상사 월드컵: http://127.0.0.1:8000', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

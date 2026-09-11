# 최악의 직장상사 월드컵

8강 → 4강 → 결승에서 더 최악인 상사를 선택하는 간단한 앱입니다.

## Streamlit 실행

Python 3.12 또는 3.13 환경에서:

```sh
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Streamlit Community Cloud 배포

https://share.streamlit.io 에서 GitHub 계정으로 로그인하고 Create app을 선택하세요.

- Repository: kfcc018-cell/myapp
- Branch: main
- Main file path: streamlit_app.py

Deploy를 누르면 requirements.txt의 의존성이 설치되고 앱이 실행됩니다.

## 기존 HTML/Python 서버 실행

별도 패키지 없이 `python server.py` 실행 후 http://127.0.0.1:8000 으로 접속합니다.

후보 8명은 server.py의 BOSSES에서 수정하세요.
Streamlit은 방문자별 세션에 게임 진행 상태를 보관하며 결과는 영구 저장하지 않습니다.

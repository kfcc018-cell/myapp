# 최악의 직장상사 월드컵

Supabase의 `boss_worldcup_items` 후보 전체로 진행하며, 우승 결과를 `boss_worldcup_results`에 저장하고 `boss_worldcup_rankings`의 우승 횟수·비율을 보여줍니다. 현재 후보는 32개입니다. 홀수 후보는 무작위 대진 마지막 후보가 부전승합니다.

## Streamlit Cloud

- Repository: `kfcc018-cell/myapp`
- Branch: `main`
- Main file: `streamlit_app.py`
- App settings → Secrets에 다음을 등록합니다.

```toml
SUPABASE_URL = "https://uvkdwnedqxgczeterdef.supabase.co"
SUPABASE_SECRET_KEY = "Supabase 프로젝트의 서버용 secret key"
```

Supabase 대시보드 → Project Settings → API Keys에서 서버용 secret key를 확인합니다. 기존 JWT service_role 키는 `SUPABASE_SERVICE_ROLE_KEY` 이름으로 등록해도 됩니다. 키는 GitHub나 브라우저 코드에 넣지 않습니다. 키를 등록해야 실제 후보 조회와 결과 저장이 작동합니다.

## 로컬 실행

Python 3.12 또는 3.13에서:

```sh
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

로컬 설정은 `.streamlit/secrets.example.toml`을 `.streamlit/secrets.toml`로 복사하고 값을 채웁니다. 실제 secrets 파일은 Git에서 제외됩니다.

기존 HTML 화면은 `python server.py` 실행 후 http://127.0.0.1:8000 에서 사용합니다. 이 서버도 동일한 Secrets를 읽거나 `SUPABASE_SECRET_KEY` 환경 변수를 사용합니다. HTML 서버의 진행 중 게임은 메모리에 있으며 서버 재시작 시 초기화됩니다.

## 저장 및 통계

- UUID 게임 ID당 우승 결과 1건만 저장합니다.
- 네트워크 실패 시 같은 ID로 재시도하므로 중복 집계하지 않습니다.
- 저장에 실패하면 결과 화면에서 재시도합니다. 저장 완료 후 새 게임을 시작할 수 있습니다.
- 통계는 누적 완료 게임 대비 후보별 우승 횟수와 비율입니다.
- 데이터베이스는 서버 전용 접근을 유지합니다. 익명 사용자의 DB 직접 수정·삭제·추가는 허용하지 않습니다.
- 로그인 없는 게임으로, 동일 사용자의 여러 게임 참여는 허용합니다.

## 테스트

```sh
python -m unittest discover -s tests
```

앱 및 HTTP 테스트는 Supabase 호출을 대체하여 실제 통계를 오염시키지 않습니다. 실제 DB의 저장·집계·중복 방지는 별도 롤백 트랜잭션으로 검증했습니다.

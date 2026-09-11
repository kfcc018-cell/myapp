import random
from uuid import uuid4

import streamlit as st
from database import DatabaseError, get_bosses, get_rankings, save_result

st.set_page_config(page_title='최악의 직장상사 월드컵', page_icon='🏆', layout='centered')


def start():
    try:
        candidates = get_bosses()
    except DatabaseError as exc:
        st.session_state.load_error = str(exc)
        return
    st.session_state.update(current=random.sample(candidates, len(candidates)),
                            winners=[], match=0, champion=None, saved=False,
                            game_id=str(uuid4()), total=len(candidates), load_error=None)


def choose(boss):
    s = st.session_state
    s.winners.append(boss)
    s.match += 1
    if s.match == len(s.current) // 2:
        if len(s.current) % 2:
            s.winners.append(s.current[-1])
        if len(s.winners) == 1:
            s.champion = s.winners[0]
        else:
            s.current, s.winners, s.match = s.winners, [], 0


st.caption('OFFICE WORLD CUP')
st.title('최악의 직장상사 월드컵')
st.write('같이 일하기 더 싫은 상사를 골라주세요.')
if 'current' not in st.session_state:
    start()
if st.session_state.get('load_error'):
    st.error(st.session_state.load_error)
    st.button('후보 다시 불러오기', on_click=start)
    st.stop()
s = st.session_state
if s.champion:
    st.subheader('🏆 최악의 상사 우승')
    with st.container(border=True):
        st.title(s.champion['emoji'])
        st.subheader(s.champion['name'])
    if not s.saved:
        try:
            save_result(s.game_id, s.champion['id'])
            s.saved = True
        except DatabaseError as exc:
            st.error(str(exc))
            st.button('저장 다시 시도')
    if s.saved:
        st.success('우승 결과가 저장됐습니다.')
    st.subheader('전체 우승 통계')
    try:
        rankings = get_rankings()
        st.metric('누적 완료 게임', sum(row['win_count'] for row in rankings))
        st.dataframe([{'상사 유형': r['content'], '우승 횟수': r['win_count'],
                       '우승 비율 (%)': float(r['win_percentage'])} for r in rankings],
                     hide_index=True, use_container_width=True)
    except DatabaseError as exc:
        st.error(str(exc))
    st.button('통계 새로고침')
    if s.saved:
        st.button('다시 하기 ↻', on_click=start, type='primary')
else:
    size = len(s.current)
    stage = '결승' if size == 2 else f'{size}강'
    st.subheader(f'{stage} · {s.match + 1} / {size // 2}')
    st.progress((s.total - size + s.match) / (s.total - 1))
    if size % 2:
        st.caption('후보 수가 홀수이면 무작위 대진의 마지막 후보가 부전승합니다.')
    for side, column in enumerate(st.columns(2)):
        boss = s.current[s.match * 2 + side]
        with column:
            with st.container(border=True):
                st.title(boss['emoji'])
                st.subheader(boss['name'])
                st.button('이 상사가 더 최악', key=f'pick_{size}_{s.match}_{side}',
                          on_click=choose, args=(boss,), use_container_width=True)
st.caption(f'가상의 상사 유형으로 즐기는 월드컵 · {s.total}명 · 총 {s.total - 1}번의 선택')

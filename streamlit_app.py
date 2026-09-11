import random

import streamlit as st

from server import BOSSES

st.set_page_config(page_title="최악의 직장상사 월드컵", page_icon="🏆", layout="centered")


def start():
    st.session_state.current = random.sample(BOSSES, len(BOSSES))
    st.session_state.winners = []
    st.session_state.match = 0
    st.session_state.champion = None


def choose(boss):
    st.session_state.winners.append(boss)
    st.session_state.match += 1
    if st.session_state.match == len(st.session_state.current) // 2:
        if len(st.session_state.winners) == 1:
            st.session_state.champion = st.session_state.winners[0]
        else:
            st.session_state.current = st.session_state.winners
            st.session_state.winners = []
            st.session_state.match = 0


if "current" not in st.session_state:
    start()

st.caption("OFFICE WORLD CUP")
st.title("최악의 직장상사 월드컵")
st.write("같이 일하기 더 싫은 상사를 골라주세요. 8명 중 최악의 상사를 찾아봅니다.")

if st.session_state.champion:
    boss = st.session_state.champion
    st.subheader("🏆 최악의 상사 우승")
    with st.container(border=True):
        st.title(boss["emoji"])
        st.subheader(boss["name"])
        st.write(boss["description"])
    st.button("다시 하기 ↻", on_click=start, type="primary")
else:
    size = len(st.session_state.current)
    stage = "결승" if size == 2 else f"{size}강"
    st.subheader(f"{stage} · {st.session_state.match + 1} / {size // 2}")
    completed = len(BOSSES) - size + st.session_state.match
    st.progress(completed / (len(BOSSES) - 1))
    for side, column in enumerate(st.columns(2)):
        boss = st.session_state.current[st.session_state.match * 2 + side]
        with column:
            with st.container(border=True):
                st.title(boss["emoji"])
                st.subheader(boss["name"])
                st.write(boss["description"])
                st.button("이 상사가 더 최악", key=f"pick_{size}_{st.session_state.match}_{side}", on_click=choose, args=(boss,), use_container_width=True)

st.caption("가상의 상사 유형으로 즐기는 월드컵 · 총 7번의 선택 · 결과는 저장하지 않습니다")

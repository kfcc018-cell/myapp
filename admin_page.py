import streamlit as st
from admin_upload import create_item
from database import DatabaseError


def show_admin():
    st.title('항목 관리')
    st.caption('누구나 새로운 항목과 사진을 등록할 수 있습니다.')
    with st.form('new_item', clear_on_submit=True):
        content = st.text_input('상사 유형 / 항목 설명', max_chars=200, placeholder='예: 퇴근 직전에 일을 주는 상사')
        photo = st.file_uploader('사진 선택', type=['jpg', 'jpeg', 'png', 'webp'], help='5MB 이하 · JPG, PNG, WEBP')
        submitted = st.form_submit_button('항목 등록', type='primary')
    if submitted:
        try:
            if photo is None:
                raise ValueError('사진을 선택해주세요.')
            with st.spinner('사진과 항목을 저장하고 있습니다…'):
                create_item(content, photo.getvalue())
            st.success('등록했습니다. 새 게임부터 후보에 포함됩니다.')
        except (ValueError, DatabaseError) as exc:
            st.error(str(exc))

import streamlit as st
from admin_upload import create_item, list_items, delete_item
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
    st.subheader('등록된 항목')
    try:
        items = list_items()
    except DatabaseError as exc:
        st.error(str(exc))
        return
    if not items:
        st.info('등록된 항목이 없습니다.')
    else:
        st.dataframe([{'ID': item['id'], '항목': item['content'], '파일명': item['filename']}
                      for item in items], hide_index=True, use_container_width=True)
        st.caption('아래 항목을 펼치면 수정하거나 삭제할 수 있습니다.')
    for item in items:
        with st.expander(f"#{item['id']} · {item['content']}"):
            st.write('파일명: ' + item['filename'])
            with st.form(f"edit_{item['id']}"):
                updated = st.text_input('항목 설명', value=item['content'], max_chars=200)
                replacement = st.file_uploader('사진 교체 (선택)', type=['jpg', 'jpeg', 'png', 'webp'])
                if st.form_submit_button('수정 저장'):
                    try:
                        create_item(updated, replacement.getvalue() if replacement else None, item['id'])
                        st.rerun()
                    except (ValueError, DatabaseError) as exc:
                        st.error(str(exc))
            confirmed = st.checkbox('이 항목을 삭제합니다. 기존 통계는 보존됩니다.', key=f"confirm_{item['id']}")
            if st.button('삭제', key=f"delete_{item['id']}", disabled=not confirmed):
                try:
                    delete_item(item['id'])
                    st.rerun()
                except (ValueError, DatabaseError) as exc:
                    st.error(str(exc))

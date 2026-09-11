from html import escape
from pathlib import Path
from database import image_url


def boss_card(boss):
    name = escape(boss['name'], quote=True)
    url = image_url(boss.get('image_url'))
    media = (f'<img class="boss-image" src="{escape(url, quote=True)}" alt="{name}" '
             'referrerpolicy="no-referrer">' if url else
             '<div class="boss-image missing-image">이미지 없음</div>')
    css = Path(__file__).with_name('cards.css').read_text(encoding='utf-8')
    return f'<style>{css}</style><div class="boss-card">{media}<div class="boss-name">{name}</div></div>'

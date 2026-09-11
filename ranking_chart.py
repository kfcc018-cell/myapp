"""Accessible horizontal ranking bars, with escaped database labels."""
from html import escape
from pathlib import Path


def ranking_chart(rows):
    rows = sorted(rows, key=lambda r: (-int(r['win_count']), int(r['winner_id'])))
    maximum = max((int(r['win_count']) for r in rows), default=0)
    parts = ['<style>' + Path(__file__).with_name('stats.css').read_text(encoding='utf-8') + '</style>',
             '<div class="ranking-chart" role="list" aria-label="우승 횟수 순위">']
    if not maximum:
        parts.append('<p>아직 집계된 우승 기록이 없습니다.</p>')
    for row in rows:
        count = int(row['win_count'])
        width = count / maximum * 100 if maximum else 0
        label = escape(str(row['content']))
        value = f"{count:,}회 · {float(row['win_percentage']):.2f}%"
        parts.append(f'<div class="ranking-row" role="listitem"><div class="ranking-label">'
                     f'<span>{label}</span><strong>{value}</strong></div>'
                     f'<div class="ranking-track" aria-hidden="true"><div class="ranking-bar" '
                     f'style="width:{width:.4f}%"></div></div></div>')
    parts.append('</div>')
    return ''.join(parts)

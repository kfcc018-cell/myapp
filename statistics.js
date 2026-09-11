async function refresh() {
  const status = document.getElementById('status');
  const button = document.getElementById('refresh');
  button.disabled = true;
  status.textContent = '불러오는 중…';
  try {
    const response = await fetch('/api/rankings');
    const rows = await response.json();
    if (!response.ok) throw new Error(rows.error || '통계를 불러오지 못했습니다.');
    rows.sort((a,b) => b.win_count - a.win_count || a.winner_id - b.winner_id);
    const maximum = Math.max(0, ...rows.map(r => r.win_count));
    const chart = document.getElementById('chart'); chart.replaceChildren();
    for (const row of rows) {
      const item = document.createElement('div'); item.className='ranking-row'; item.setAttribute('role','listitem');
      const label = document.createElement('div'); label.className='ranking-label';
      const name = document.createElement('span'); name.textContent=row.content;
      const value = document.createElement('strong'); value.textContent=`${row.win_count}회 · ${Number(row.win_percentage).toFixed(2)}%`;
      label.append(name,value);
      const track = document.createElement('div'); track.className='ranking-track'; track.setAttribute('aria-hidden','true');
      const bar = document.createElement('div'); bar.className='ranking-bar'; bar.style.width=`${maximum ? row.win_count / maximum * 100 : 0}%`;
      track.append(bar); item.append(label,track); chart.append(item);
    }
    status.textContent = maximum ? `누적 ${rows.reduce((sum,r)=>sum+r.win_count,0)}게임` : '아직 집계된 우승 기록이 없습니다.';
  } catch (error) {status.textContent=error.message;}
  finally {button.disabled=false;}
}
document.getElementById('refresh').onclick=refresh;
refresh();

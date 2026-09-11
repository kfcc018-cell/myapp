const $ = id => document.getElementById(id);
let game = null;
let busy = false;
function card(element, boss) {
  element.replaceChildren();
  for (const [cls, text] of [['emoji', boss.emoji], ['name', boss.name]]) {
    const span = document.createElement('span');
    span.className = cls; span.textContent = text; element.append(span);
  }
}
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '요청에 실패했습니다.');
  return data;
}
function render() {
  $('choices').hidden = !!game.champion;
  $('result').hidden = !game.champion;
  $('subtitle').textContent = `${game.total}명 중 최악의 상사를 골라주세요.`;
  $('footnote').textContent = `총 ${game.total - 1}번의 선택 · 결과는 전체 통계에 반영됩니다`;
  if (game.champion) {
    $('round').textContent = '🏆 최악의 상사 우승';
    card($('winner'), game.champion);
  } else {
    $('round').textContent = `${game.size === 2 ? '결승' : game.size + '강'} · ${game.match + 1} / ${Math.floor(game.size / 2)}`;
    card($('left'), game.pair[0]); card($('right'), game.pair[1]);
  }
}
async function statistics() {
  $('statsStatus').textContent = '결과 저장 중…';
  $('refresh').disabled = true;
  $('restart').disabled = true;
  try {
    await api('/api/result', {game_id: game.game_id});
    game.saved = true;
    $('restart').disabled = false;
    $('statsStatus').textContent = '저장 완료 · 통계 불러오는 중…';
    const rows = await api('/api/rankings');
    $('statsBody').replaceChildren();
    for (const row of rows) {
      const tr = document.createElement('tr');
      for (const value of [row.content, row.win_count, row.win_percentage + '%']) {
        const td = document.createElement('td'); td.textContent = value; tr.append(td);
      }
      $('statsBody').append(tr);
    }
    $('statsStatus').textContent = `저장 완료 · 누적 ${rows.reduce((n, r) => n + r.win_count, 0)}게임`;
    $('stats').hidden = false;
  } catch (error) {
    $('statsStatus').textContent = error.message + ' 아래 버튼으로 다시 시도해주세요.';
  } finally { $('refresh').disabled = false; }
}
async function start() {
  if (busy) return;
  busy = true;
  $('error').hidden = true;
  try {
    game = await api('/api/game', {});
    $('stats').hidden = true;
    render();
  } catch (error) {
    $('errorText').textContent = error.message;
    $('error').hidden = false;
  } finally { busy = false; }
}
async function select(side) {
  if (busy || !game || game.champion) return;
  busy = true;
  $('left').disabled = $('right').disabled = true;
  $('error').hidden = true;
  $('choices').classList.add(side === 0 ? 'picked-left' : 'picked-right');
  const selected = side === 0 ? $('left') : $('right');
  const badge = document.createElement('span');
  badge.className = 'selection-badge'; badge.textContent = '✓ 선택 완료';
  selected.append(badge);
  try {
    const [next] = await Promise.all([api('/api/choose', {game_id: game.game_id, winner_id: game.pair[side].id,
      size: game.size, match: game.match}), new Promise(resolve => setTimeout(resolve, 500))]);
    game = next;
    $('choices').classList.remove('picked-left', 'picked-right');
    render();
    if (game.champion) await statistics();
  } catch (error) {
    $('errorText').textContent = error.message;
    $('error').hidden = false;
  } finally {
    $('choices').classList.remove('picked-left', 'picked-right');
    badge.remove();
    busy = false; $('left').disabled = $('right').disabled = false;
  }
}
$('left').onclick = () => select(0);
$('right').onclick = () => select(1);
$('restart').onclick = start;
$('retry').onclick = start;
$('refresh').onclick = statistics;
start();

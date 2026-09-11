const form = document.getElementById('form');
const photo = document.getElementById('photo');
const status = document.getElementById('status');
const submit = document.getElementById('submit');
const preview = document.getElementById('preview');
let previewUrl;
let editingId = null;
const cancel = document.createElement('button'); cancel.type = 'button'; cancel.textContent = '수정 취소'; cancel.hidden = true;
form.append(cancel);
cancel.onclick = () => {editingId=null; form.reset(); photo.required=true; submit.textContent='항목 등록'; cancel.hidden=true; preview.hidden=true;};
const heading = document.createElement('h2'); heading.textContent='등록된 항목';
const list = document.createElement('div');
form.parentElement.append(heading, list);
async function loadItems() {
  try {
    const response=await fetch('/api/items'); const rows=await response.json();
    if (!response.ok) throw new Error(rows.error);
    list.replaceChildren();
    if (!rows.length) list.textContent='등록된 항목이 없습니다.';
    for (const row of rows) {
      const item=document.createElement('section'); item.style.cssText='border-bottom:1px solid #555;padding:16px 0;overflow-wrap:anywhere';
      const title=document.createElement('strong'); title.textContent=`#${row.id} · ${row.content}`;
      const filename=document.createElement('p'); filename.textContent='파일명: '+row.filename;
      const edit=document.createElement('button'); edit.textContent='수정';
      edit.onclick=()=>{editingId=row.id;document.getElementById('content').value=row.content;photo.value='';photo.required=false;submit.textContent='수정 저장';cancel.hidden=false;preview.hidden=true;form.scrollIntoView({behavior:'smooth'});};
      const remove=document.createElement('button'); remove.textContent='삭제'; remove.style.marginLeft='12px';
      remove.onclick=async()=>{
        if (!confirm('이 항목을 삭제할까요? 기존 우승 통계는 보존됩니다.')) return;
        remove.disabled=true;
        try {
          const response=await fetch('/api/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'delete',id:row.id})});
          const data=await response.json();if(!response.ok) throw new Error(data.error);
          if(editingId===row.id) cancel.click();
          status.textContent='삭제했습니다.';await loadItems();
        } catch(error){status.textContent=error.message;} finally{remove.disabled=false;}
      };
      item.append(title,filename,edit,remove); list.append(item);
    }
  } catch(error){list.textContent=error.message || '목록을 불러오지 못했습니다.';}
}
photo.onchange = () => {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  const file = photo.files[0];
  preview.hidden = true;
  if (file && file.size <= 5 * 1024 * 1024) {
    previewUrl = URL.createObjectURL(file); preview.src = previewUrl; preview.hidden = false;
  }
};
form.onsubmit = async event => {
  event.preventDefault();
  const file = photo.files[0];
  if ((!file && editingId === null) || (file && file.size > 5 * 1024 * 1024)) {status.textContent = '5MB 이하의 사진을 선택해주세요.'; return;}
  submit.disabled = true; status.textContent = '등록 중…';
  try {
    const encoded = file ? await new Promise((resolve, reject) => {
      const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = () => reject(new Error('파일을 읽지 못했습니다.')); reader.readAsDataURL(file);
    }) : null;
    const response = await fetch('/api/items', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({content:document.getElementById('content').value,photo:encoded,id:editingId})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '등록하지 못했습니다.');
    status.textContent = '등록했습니다. 새 게임부터 후보에 포함됩니다.';
    cancel.click(); await loadItems();
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  } catch (error) {status.textContent = error.message;}
  finally {submit.disabled = false;}
};
loadItems();

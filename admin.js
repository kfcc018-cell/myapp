const form = document.getElementById('form');
const photo = document.getElementById('photo');
const status = document.getElementById('status');
const submit = document.getElementById('submit');
const preview = document.getElementById('preview');
let previewUrl;
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
  if (!file || file.size > 5 * 1024 * 1024) {status.textContent = '5MB 이하의 사진을 선택해주세요.'; return;}
  submit.disabled = true; status.textContent = '등록 중…';
  try {
    const encoded = await new Promise((resolve, reject) => {
      const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = () => reject(new Error('파일을 읽지 못했습니다.')); reader.readAsDataURL(file);
    });
    const response = await fetch('/api/items', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({content:document.getElementById('content').value,photo:encoded})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '등록하지 못했습니다.');
    status.textContent = '등록했습니다. 새 게임부터 후보에 포함됩니다.';
    form.reset(); preview.hidden = true;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  } catch (error) {status.textContent = error.message;}
  finally {submit.disabled = false;}
};

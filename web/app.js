const topic = document.querySelector('#topic');
const duration = document.querySelector('#duration');
const mode = document.querySelector('#mode');
const button = document.querySelector('#generate');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const output = document.querySelector('#output');

button.addEventListener('click', async () => {
  const value = topic.value.trim();
  if (!value) {
    status.textContent = 'Enter a topic first.';
    return;
  }

  result.classList.remove('hidden');
  output.textContent = '';
  status.textContent = 'Creating your generation job…';
  button.disabled = true;

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: value, duration: Number(duration.value) })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Generation request failed');

    if (data.status === 'needs_script') {
      status.textContent = 'Script prompt created.';
      output.textContent = data.script_prompt + '\n\nV1 currently keeps the AI provider separate. Paste this prompt into your preferred AI model, then we will add one-click script generation in V2.';
      return;
    }

    status.textContent = 'Short generated!';
    output.innerHTML = `<video controls playsinline style="width:100%;max-height:70vh;border-radius:12px" src="${data.video_url}"></video><p><a href="${data.video_url}" target="_blank">Open video</a> · <a href="${data.captions_url}" target="_blank">Open captions</a></p>`;
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

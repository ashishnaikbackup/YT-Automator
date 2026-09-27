const topic = document.querySelector('#topic');
const duration = document.querySelector('#duration');
const mode = document.querySelector('#mode');
const button = document.querySelector('#generate');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const output = document.querySelector('#output');
const topicHint = document.querySelector('#topicHint');

mode.addEventListener('change', () => {
  const auto = mode.value === 'auto';
  topic.disabled = auto;
  topic.placeholder = auto
    ? 'No topic needed — YT-Automator will find a current topic.'
    : 'Example: 5 free AI tools every engineering student should know';
  topicHint.textContent = auto
    ? 'Auto mode: leave the topic empty. We will discover a current topic first.'
    : 'Prompt mode: enter a topic or idea.';
});

button.addEventListener('click', async () => {
  const auto = mode.value === 'auto';
  const value = topic.value.trim();

  if (!auto && !value) {
    status.textContent = 'Enter a topic first.';
    return;
  }

  result.classList.remove('hidden');
  output.textContent = '';
  status.textContent = auto ? 'Finding a current topic…' : 'Researching your topic…';
  button.disabled = true;

  try {
    let selectedTopic = value;

    if (auto) {
      const trendResponse = await fetch('/api/trends');
      const trendData = await trendResponse.json();
      if (!trendResponse.ok || !trendData.topics?.length) {
        throw new Error(trendData.error || 'No current topics were found.');
      }

      const first = trendData.topics[0];
      selectedTopic = first.topic;
      status.textContent = `Selected topic: ${selectedTopic}`;
    }

    status.textContent = 'Generating script, voice and video…';
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: selectedTopic,
        duration: Number(duration.value),
        auto_script: true
      })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || data.hint || 'Generation request failed');

    if (data.status === 'needs_provider') {
      status.textContent = 'AI provider setup is required for this hosted deployment.';
      output.textContent = `${data.error || ''}\n\n${data.hint || ''}\n\nTopic: ${selectedTopic}`;
      return;
    }

    if (data.status === 'needs_script') {
      status.textContent = 'Script prompt created.';
      output.textContent = data.script_prompt;
      return;
    }

    status.textContent = 'Short generated!';
    output.innerHTML = `<p><strong>Topic:</strong> ${selectedTopic}</p><video controls playsinline style="width:100%;max-height:70vh;border-radius:12px" src="${data.video_url}"></video><p><a href="${data.video_url}" target="_blank">Open video</a> · <a href="${data.captions_url}" target="_blank">Open captions</a></p>`;
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

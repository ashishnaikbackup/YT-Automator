const topic = document.querySelector('#topic');
const duration = document.querySelector('#duration');
const mode = document.querySelector('#mode');
const button = document.querySelector('#generate');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const output = document.querySelector('#output');

button.addEventListener('click', () => {
  const value = topic.value.trim();
  if (!value) {
    status.textContent = 'Enter a topic first.';
    return;
  }

  result.classList.remove('hidden');
  status.textContent = 'Preparing generation request…';
  output.textContent = [
    `Topic: ${value}`,
    `Duration: ${duration.value}s`,
    `Mode: ${mode.value}`,
    '',
    'The web UI is ready. The server-side generation endpoint will be connected next.',
    'V2 will add automatic research and trend discovery.'
  ].join('\n');
});

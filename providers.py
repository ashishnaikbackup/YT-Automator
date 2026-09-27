from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def ollama_generate(prompt: str, model: str | None = None) -> str:
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Local Ollama is unavailable. Install/run Ollama or provide narration manually.") from exc
    text = str(data.get("response", "")).strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response.")
    return text

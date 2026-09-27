from __future__ import annotations

import os
import requests


def generate_script(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "gemini":
        return _gemini(prompt)
    if provider == "ollama":
        return _ollama(prompt)
    raise RuntimeError("Unsupported LLM_PROVIDER. Use 'ollama' or 'gemini'.")


def _ollama(prompt: str) -> str:
    base = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    response = requests.post(
        f"{base.rstrip('/')}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=180,
    )
    response.raise_for_status()
    text = response.json().get("response", "").strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response")
    return text


def _gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    response = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=120,
    )
    response.raise_for_status()
    candidates = response.json().get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    return candidates[0]["content"]["parts"][0]["text"].strip()

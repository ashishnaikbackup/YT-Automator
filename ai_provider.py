from __future__ import annotations

import os
import requests


def generate_script(topic: str, duration: int, research: str = "") -> str:
    """Generate narration with a configured OpenAI-compatible endpoint.

    If no API key is configured, return an explicit message so the UI can fall back
    to showing the generated prompt instead of pretending the script was generated.
    """
    api_key = os.getenv("AI_API_KEY", "").strip()
    endpoint = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions").strip()
    model = os.getenv("AI_MODEL", "gpt-4o-mini").strip()

    if not api_key:
        raise RuntimeError("No AI_API_KEY configured. Set an OpenAI-compatible provider key or use prompt-only mode.")

    prompt = f"""Write a YouTube Short narration about: {topic}\nTarget duration: {duration} seconds.\nUse a strong hook, simple spoken English, useful factual information, and a short CTA. Return only narration.\n\nResearch sources:\n{research}"""
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.6},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()

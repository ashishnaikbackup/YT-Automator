import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OUTPUT_DIR = Path("outputs")


def clean_script(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"\([^\n]*?(?:music|appears|screen|shot|host|visual|animation)[^\n]*\)", "", text, flags=re.I)
    text = re.sub(r"\*\*.*?\*\*", "", text)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^(Host|Narrator|Voiceover)\s*:\s*", "", line, flags=re.I)
        if line.strip() and not re.match(r"^(Here(?:'s| is)|Note:|Script:)", line.strip(), re.I):
            lines.append(line.strip())
    return " ".join(lines).strip()


def generate_script(topic: str, duration: int) -> str:
    prompt = f"""Write ONLY the spoken narration for a YouTube Short about: {topic}\n\nTarget duration: {duration} seconds.\nRules:\n- Start with a strong hook.\n- Use simple, natural spoken English.\n- Fast pacing.\n- Give useful factual information.\n- Do not invent statistics, quotes, products, features, or events.\n- If a claim is uncertain, omit it.\n- End with a short call to action.\n- NO headings.\n- NO stage directions.\n- NO speaker labels.\n- NO notes.\nReturn narration only."""
    r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=300)
    r.raise_for_status()
    return clean_script(r.json().get("response", ""))


def make_tts(text: str, wav_path: Path):
    # Windows built-in SAPI voice: no API key and no cloud bill.
    ps = f'''Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate=1; $s.Volume=100; $s.SetOutputToWaveFile('{wav_path.resolve()}'); $s.Speak(@'{text.replace("'", "''")}'@); $s.Dispose()'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def make_video(audio: Path, script: str, out_path: Path, duration: int):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed or not on PATH. Install FFmpeg, then reopen Command Prompt.")
    # A clean dark vertical canvas with readable timed text. This keeps V1 fully local/free.
    vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,drawtext=text='YT-Automator':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=180"
    cmd = [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30", "-i", str(audio), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_path)]
    subprocess.run(cmd, check=True)


def generate_short(topic: str, duration: int):
    job = uuid.uuid4().hex[:10]
    job_dir = OUTPUT_DIR / job
    job_dir.mkdir(parents=True, exist_ok=True)
    script = generate_script(topic, duration)
    (job_dir / "script.txt").write_text(script, encoding="utf-8")
    audio = job_dir / "voice.wav"
    make_tts(script, audio)
    final = job_dir / "final_short.mp4"
    make_video(audio, script, final, duration)
    return {"job_id": job, "script": script, "video_url": f"/outputs/{job}/final_short.mp4"}

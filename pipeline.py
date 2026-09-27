import os
import re
import shutil
import subprocess
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
    prompt = f"""Write ONLY the spoken narration for a YouTube Short about: {topic}

Target duration: {duration} seconds.
Rules:
- Start with a strong hook.
- Use simple, natural spoken English.
- Fast pacing.
- Give useful factual information.
- Do not invent statistics, quotes, products, features, or events.
- If a claim is uncertain, omit it.
- End with a short call to action.
- NO headings.
- NO stage directions.
- NO speaker labels.
- NO notes.
Return narration only."""
    r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=300)
    r.raise_for_status()
    return clean_script(r.json().get("response", ""))


def make_tts(text: str, wav_path: Path):
    # Use a temporary UTF-8 text file instead of embedding the narration
    # directly inside a PowerShell command. This safely handles apostrophes,
    # quotes, punctuation, and multi-line text on Windows.
    text_path = wav_path.with_suffix(".txt")
    text_path.write_text(text, encoding="utf-8")
    env = os.environ.copy()
    env["YT_AUTOMATOR_TEXT"] = str(text_path.resolve())
    env["YT_AUTOMATOR_WAV"] = str(wav_path.resolve())
    ps = "Add-Type -AssemblyName System.Speech; $text=[System.IO.File]::ReadAllText($env:YT_AUTOMATOR_TEXT,[System.Text.Encoding]::UTF8); $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate=1; $s.Volume=100; $s.SetOutputToWaveFile($env:YT_AUTOMATOR_WAV); $s.Speak($text); $s.Dispose()"
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True, env=env)


def ffmpeg_path():
    direct = shutil.which("ffmpeg")
    if direct:
        return direct
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("FFmpeg is missing. Run run_local.bat again so the free local FFmpeg package can be installed.") from exc


def make_srt(script: str, srt_path: Path, duration: int):
    words = script.split()
    if not words:
        raise RuntimeError("Ollama returned an empty script.")
    chunks = [" ".join(words[i:i + 7]) for i in range(0, len(words), 7)]
    total = max(duration, 1)
    step = total / len(chunks)
    lines = []
    for i, chunk in enumerate(chunks):
        start = i * step
        end = min(total, (i + 1) * step)
        def ts(sec):
            ms = int(round((sec - int(sec)) * 1000))
            whole = int(sec)
            h, rem = divmod(whole, 3600)
            m, s = divmod(rem, 60)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"
        lines += [str(i + 1), f"{ts(start)} --> {ts(end)}", chunk, ""]
    srt_path.write_text("\n".join(lines), encoding="utf-8")


def make_video(audio: Path, srt: Path, out_path: Path):
    ffmpeg = ffmpeg_path()
    subtitle_file = str(srt.resolve()).replace("\\", "/").replace(":", "\\:")
    vf = f"drawtext=text='YT-Automator':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=150,subtitles='{subtitle_file}'"
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
    srt = job_dir / "captions.srt"
    make_srt(script, srt, duration)
    final = job_dir / "final_short.mp4"
    make_video(audio, srt, final)
    return {"job_id": job, "script": script, "video_url": f"/outputs/{job}/final_short.mp4"}

import html
import os
import re
import shutil
import subprocess
import uuid
import wave
from pathlib import Path

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OUTPUT_DIR = Path("outputs")
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


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
- Start with a strong 1-sentence hook.
- Use simple, natural, energetic spoken English.
- Keep sentences short and punchy.
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
    text_path = wav_path.with_suffix(".txt")
    text_path.write_text(text, encoding="utf-8")
    env = os.environ.copy()
    env["YT_AUTOMATOR_TEXT"] = str(text_path.resolve())
    env["YT_AUTOMATOR_WAV"] = str(wav_path.resolve())
    ps = r'''Add-Type -AssemblyName System.Speech;
$text=[System.IO.File]::ReadAllText($env:YT_AUTOMATOR_TEXT,[System.Text.Encoding]::UTF8);
$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;
$voices=$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo };
$preferred=$voices | Where-Object { $_.Name -match 'Zira|Jenny|Aria|Samantha' -and $_.Culture.Name -match '^en-' } | Select-Object -First 1;
if($preferred){$s.SelectVoice($preferred.Name)}
$s.Rate=2;
$s.Volume=100;
$s.SetOutputToWaveFile($env:YT_AUTOMATOR_WAV);
$s.Speak($text);
$s.Dispose()'''
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True, env=env)


def audio_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as w:
        return max(0.1, w.getnframes() / float(w.getframerate()))


def ffmpeg_path():
    direct = shutil.which("ffmpeg")
    if direct:
        return direct
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("FFmpeg is missing. Run run_local.bat again so the free local FFmpeg package can be installed.") from exc


def commons_image(query: str, session: requests.Session):
    params = {"action": "query", "format": "json", "formatversion": "2", "generator": "search", "gsrsearch": query,
              "gsrnamespace": 6, "gsrwhat": "text", "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1080}
    r = session.get(COMMONS_API, params=params, timeout=20)
    r.raise_for_status()
    for page in r.json().get("query", {}).get("pages", []):
        info = (page.get("imageinfo") or [{}])[0]
        mime = info.get("mime", "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        meta = info.get("extmetadata", {})
        license_name = html.unescape(meta.get("LicenseShortName", {}).get("value", ""))
        license_low = license_name.lower()
        if not ("public domain" in license_low or "cc0" in license_low or license_low.startswith("cc by")):
            continue
        title = page.get("title", "")
        return {"title": title, "url": info.get("thumburl") or info.get("url"),
                "source": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
                "license": license_name, "artist": html.unescape(meta.get("Artist", {}).get("value", ""))}
    return None


def download_visuals(topic: str, script: str, job_dir: Path, count: int = 6):
    session = requests.Session()
    session.headers.update({"User-Agent": "YT-Automator/1.0 (local video generator)"})
    queries = [topic] + [s[:100] for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
    visuals, seen = [], set()
    for query in queries:
        if len(visuals) >= count:
            break
        try:
            item = commons_image(query, session)
            if not item or item["title"] in seen or not item["url"]:
                continue
            response = session.get(item["url"], timeout=30)
            response.raise_for_status()
            path = job_dir / f"visual_{len(visuals)+1}.jpg"
            path.write_bytes(response.content)
            item["path"] = path
            visuals.append(item)
            seen.add(item["title"])
        except requests.RequestException:
            continue
    if visuals:
        credits = ["YT-Automator visual sources", ""]
        credits += [f"{x['title']} | {x['license']} | {x['artist']} | {x['source']}" for x in visuals]
        (job_dir / "visual_credits.txt").write_text("\n".join(credits), encoding="utf-8")
    return visuals


def make_visual_video(images, out_path: Path, duration: float):
    ffmpeg = ffmpeg_path()
    if not images:
        subprocess.run([ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=0x11131a:s=1080x1920:r=30", "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)], check=True)
        return
    clip_dir = out_path.parent / "clips"
    clip_dir.mkdir(exist_ok=True)
    each = duration / len(images)
    clips = []
    for i, image in enumerate(images):
        clip = clip_dir / f"clip_{i+1}.mp4"
        vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              "zoompan=z='min(zoom+0.0008,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p")
        subprocess.run([ffmpeg, "-y", "-loop", "1", "-i", str(image["path"]), "-t", f"{each:.3f}", "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(clip)], check=True)
        clips.append(clip)
    concat = clip_dir / "concat.txt"
    concat.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in clips), encoding="utf-8")
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-t", f"{duration:.3f}", str(out_path)], check=True)


def make_ass(script: str, ass_path: Path, duration: float):
    words = script.split()
    if not words:
        raise RuntimeError("Ollama returned an empty script.")
    chunks = [" ".join(words[i:i + 5]) for i in range(0, len(words), 5)]
    weights = [len(c.split()) for c in chunks]
    total_weight = sum(weights)
    def ts(sec):
        h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); cs = int(round((sec - int(sec)) * 100))
        if cs == 100: s += 1; cs = 0
        return f"{h}:{m:02}:{s:02}.{cs:02}"
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "ScaledBorderAndShadow: yes", "",
             "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: Short,Arial,70,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H99000000,1,0,3,12,0,2,70,70,220,1", "",
             "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    cursor = 0.0
    for chunk, weight in zip(chunks, weights):
        end = min(duration, cursor + duration * weight / total_weight)
        safe = chunk.replace("{", "\\{").replace("}", "\\}")
        lines.append(f"Dialogue: 0,{ts(cursor)},{ts(end)},Short,,0,0,0,,{safe}")
        cursor = end
    ass_path.write_text("\n".join(lines), encoding="utf-8")


def make_video(visual_video: Path, audio: Path, ass: Path, out_path: Path, duration: float):
    ffmpeg = ffmpeg_path()
    ass_file = str(ass.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    subprocess.run([ffmpeg, "-y", "-i", str(visual_video), "-i", str(audio), "-vf", f"ass='{ass_file}'", "-map", "0:v:0", "-map", "1:a:0", "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_path)], check=True)


def generate_short(topic: str, duration: int):
    job = uuid.uuid4().hex[:10]
    job_dir = OUTPUT_DIR / job
    job_dir.mkdir(parents=True, exist_ok=True)
    script = generate_script(topic, duration)
    (job_dir / "script.txt").write_text(script, encoding="utf-8")
    audio = job_dir / "voice.wav"
    make_tts(script, audio)
    actual_duration = audio_duration(audio)
    visuals = download_visuals(topic, script, job_dir)
    visual_video = job_dir / "visuals.mp4"
    make_visual_video(visuals, visual_video, actual_duration)
    ass = job_dir / "captions.ass"
    make_ass(script, ass, actual_duration)
    final = job_dir / "final_short.mp4"
    make_video(visual_video, audio, ass, final, actual_duration)
    return {"job_id": job, "script": script, "visual_count": len(visuals), "duration": round(actual_duration, 1), "video_url": f"/outputs/{job}/final_short.mp4"}

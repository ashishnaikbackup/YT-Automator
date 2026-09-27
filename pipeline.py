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
OPENVERSE_API = "https://api.openverse.org/v1/images/"


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
- Sound like a real young YouTube creator speaking naturally: conversational, confident, upbeat and energetic.
- Use short punchy sentences, contractions, and occasional emphasis words.
- Keep the pacing lively from beginning to end; do not add a slow middle section.
- Give useful factual information.
- Do not invent statistics, quotes, products, features, or events.
- If a claim is uncertain, omit it.
- End with a very short call to action.
- NO headings, stage directions, speaker labels, notes, emojis, or sound effects.
Return narration only."""
    r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=300)
    r.raise_for_status()
    return clean_script(r.json().get("response", ""))


def ffmpeg_path():
    direct = shutil.which("ffmpeg")
    if direct:
        return direct
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("FFmpeg is missing. Run run_local.bat again so the free local FFmpeg package can be installed.") from exc


def make_tts(text: str, wav_path: Path):
    """Use Microsoft's free Edge neural TTS voices when internet is available.
    Fall back to Windows Speech if Edge TTS cannot be reached."""
    ffmpeg = ffmpeg_path()
    mp3_path = wav_path.with_suffix(".mp3")
    try:
        import asyncio
        import edge_tts

        async def synthesize():
            communicate = edge_tts.Communicate(
                text,
                "en-US-AndrewMultilingualNeural",
                rate="+12%",
                pitch="+2Hz",
                volume="+0%",
            )
            await communicate.save(str(mp3_path))

        asyncio.run(synthesize())
        subprocess.run([ffmpeg, "-y", "-i", str(mp3_path), "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)], check=True)
        return
    except Exception as exc:
        print(f"Edge neural voice unavailable, using Windows voice fallback: {exc}")

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
$s.Rate=3;
$s.Volume=100;
$s.SetOutputToWaveFile($env:YT_AUTOMATOR_WAV);
$s.Speak($text);
$s.Dispose()'''
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True, env=env)


def audio_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as w:
        return max(0.1, w.getnframes() / float(w.getframerate()))


def openverse_image(query: str, session: requests.Session):
    """Find a reusable image through Openverse (CC/public-domain sources)."""
    params = {
        "q": query,
        "page_size": 20,
        "license_type": "commercial",
    }
    r = session.get(OPENVERSE_API, params=params, timeout=25)
    r.raise_for_status()
    for item in r.json().get("results", []):
        license_code = (item.get("license") or "").lower()
        if license_code not in {"cc0", "by", "by-sa", "by-nc", "by-nc-sa", "by-nd", "by-nc-nd"}:
            continue
        url = item.get("thumbnail") or item.get("url")
        if not url:
            continue
        return {
            "title": item.get("title") or query,
            "url": url,
            "source": item.get("foreign_landing_url") or item.get("url") or "https://openverse.org/",
            "license": (item.get("license") or "").upper(),
            "artist": item.get("creator") or "",
        }
    return None


def commons_search(query: str, session: requests.Session):
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "search", "gsrsearch": query, "gsrnamespace": 6,
        "gsrwhat": "text", "gsrlimit": 30,
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1080,
    }
    r = session.get(COMMONS_API, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("query", {}).get("pages", [])


def commons_image(query: str, session: requests.Session):
    for page in commons_search(query, session):
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
        return {
            "title": title,
            "url": info.get("thumburl") or info.get("url"),
            "source": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
            "license": license_name,
            "artist": html.unescape(meta.get("Artist", {}).get("value", "")),
        }
    return None


def visual_queries(topic: str, script: str):
    """Create short, image-search-friendly queries instead of sending full sentences."""
    text = f"{topic} {script}".lower()
    stop = set("a an the and or but for with from into about this that these those are is was were be been being to of in on at by as it its your you we they their our can will how why what when where which have has had do does did not no very really just more most some any all three free tool tools students student engineering engineers learn learning next first second third last now get use using help useful".split())
    words = re.findall(r"[a-z][a-z0-9-]+", text)
    terms = []
    for w in words:
        if w not in stop and len(w) >= 4 and w not in terms:
            terms.append(w)
    queries = [topic.strip()]
    if any(x in text for x in ["ai", "artificial intelligence", "machine learning", "llm", "ollama", "chatbot"]):
        queries += ["artificial intelligence", "machine learning", "computer programming", "robot artificial intelligence"]
    if any(x in text for x in ["engineering", "engineer", "student", "college"]):
        queries += ["engineering students", "engineering laboratory", "computer engineering"]
    for i in range(0, min(len(terms), 12), 2):
        if i + 1 < len(terms):
            queries.append(f"{terms[i]} {terms[i+1]}")
        else:
            queries.append(terms[i])
    out, seen = [], set()
    for q in queries:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q.lower() not in seen:
            out.append(q[:80]); seen.add(q.lower())
    return out


def download_visuals(topic: str, script: str, job_dir: Path, count: int = 8):
    """Download genuinely reusable visuals, preferring Openverse and falling back to Commons."""
    session = requests.Session()
    session.headers.update({"User-Agent": "YT-Automator/1.2 (local video generator; visual retrieval)"})
    visuals, seen = [], set()
    for query in visual_queries(topic, script):
        if len(visuals) >= count:
            break
        item = None
        try:
            item = openverse_image(query, session)
        except requests.RequestException as exc:
            print(f"Openverse search failed for '{query}': {exc}")
        if item is None:
            try:
                item = commons_image(query, session)
            except requests.RequestException as exc:
                print(f"Commons search failed for '{query}': {exc}")
        if not item or item["title"] in seen or not item["url"]:
            continue
        try:
            response = session.get(item["url"], timeout=30)
            response.raise_for_status()
            if len(response.content) < 5000:
                continue
            path = job_dir / f"visual_{len(visuals)+1}.jpg"
            path.write_bytes(response.content)
            item["path"] = path
            visuals.append(item)
            seen.add(item["title"])
            print(f"Visual {len(visuals)}/{count}: {query} -> {item['title']}")
        except requests.RequestException as exc:
            print(f"Visual download failed for '{query}': {exc}")
            continue
    if not visuals:
        raise RuntimeError("No usable free visuals were found. Check your internet connection and try again.")
    credits = ["YT-Automator visual sources", ""]
    credits += [f"{x['title']} | {x['license']} | {x['artist']} | {x['source']}" for x in visuals]
    (job_dir / "visual_credits.txt").write_text("\n".join(credits), encoding="utf-8")
    return visuals


def make_visual_video(images, out_path: Path, duration: float):
    ffmpeg = ffmpeg_path()
    clip_dir = out_path.parent / "clips"
    clip_dir.mkdir(exist_ok=True)
    each = duration / len(images)
    clips = []
    for i, image in enumerate(images):
        clip = clip_dir / f"clip_{i+1}.mp4"
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "zoompan=z='min(zoom+0.0012,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            "d=1:s=1080x1920:fps=30,format=yuv420p"
        )
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
    visuals = download_visuals(topic, script, job_dir, count=8)
    visual_video = job_dir / "visuals.mp4"
    make_visual_video(visuals, visual_video, actual_duration)
    ass = job_dir / "captions.ass"
    make_ass(script, ass, actual_duration)
    final = job_dir / "final_short.mp4"
    make_video(visual_video, audio, ass, final, actual_duration)
    return {"job_id": job, "script": script, "visual_count": len(visuals), "duration": round(actual_duration, 1), "video_url": f"/outputs/{job}/final_short.mp4"}

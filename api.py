import os
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from config import OUTPUTS
from script_generator import build_script_prompt
from voice import generate_voice
from captions import create_srt
from renderer import render_short
from research import search_news, format_research
from trends import discover_topics
from llm import generate_script

app = Flask(__name__, static_folder="web", static_url_path="")

@app.get("/")
def index():
    return send_from_directory("web", "index.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "YT-Automator"})

@app.get("/api/research")
def research():
    query = request.args.get("q", "AI tools for students").strip()
    try:
        return jsonify({"query": query, "results": search_news(query)})
    except Exception as exc:
        return jsonify({"error": f"research failed: {exc}"}), 502

@app.get("/api/trends")
def trends():
    return jsonify({"topics": discover_topics()})

@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    duration = int(data.get("duration", 45))
    narration = str(data.get("narration", "")).strip()
    auto_script = bool(data.get("auto_script", True))

    if not topic:
        return jsonify({"error": "topic is required"}), 400
    if duration < 15 or duration > 180:
        return jsonify({"error": "duration must be between 15 and 180 seconds"}), 400

    job_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    job_dir = OUTPUTS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        sources = search_news(topic)
    except Exception:
        sources = []

    prompt = build_script_prompt(topic, duration, sources)
    research_text = format_research(sources)
    (job_dir / "research.txt").write_text(research_text + "\n", encoding="utf-8")
    (job_dir / "script_prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    if not narration and auto_script:
        try:
            narration = generate_script(prompt)
        except Exception as exc:
            return jsonify({
                "job_id": job_id,
                "status": "needs_provider",
                "script_prompt": prompt,
                "sources": sources,
                "error": str(exc),
                "hint": "Set LLM_PROVIDER=ollama for a local free model, or configure GEMINI_API_KEY for Gemini.",
            }), 503

    if not narration:
        return jsonify({"job_id": job_id, "status": "needs_script", "script_prompt": prompt, "sources": sources})

    script_path = job_dir / "script.txt"
    script_path.write_text(narration + "\n", encoding="utf-8")
    audio_path = job_dir / "voice.mp3"
    generate_voice(narration, audio_path)

    from moviepy import AudioFileClip
    audio = AudioFileClip(str(audio_path))
    actual_duration = audio.duration
    audio.close()

    srt_path = job_dir / "captions.srt"
    create_srt(narration, actual_duration, srt_path)
    video_path = job_dir / "final_short.mp4"
    render_short(narration, audio_path, video_path)

    return jsonify({"job_id": job_id, "status": "complete", "script": narration, "video_url": f"/api/jobs/{job_id}/final_short.mp4", "captions_url": f"/api/jobs/{job_id}/captions.srt", "sources": sources})

@app.get("/api/jobs/<job_id>/<path:filename>")
def job_file(job_id, filename):
    return send_from_directory(str(OUTPUTS / job_id), filename, as_attachment=False)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)

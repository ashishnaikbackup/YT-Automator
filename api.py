from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from config import OUTPUTS
from script_generator import build_script_prompt
from voice import generate_voice
from captions import create_srt
from renderer import render_short

app = Flask(__name__, static_folder="web", static_url_path="")


@app.get("/")
def index():
    return send_from_directory("web", "index.html")


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    duration = int(data.get("duration", 45))
    narration = str(data.get("narration", "")).strip()

    if not topic:
        return jsonify({"error": "topic is required"}), 400

    job_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    job_dir = OUTPUTS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_script_prompt(topic, duration)
    (job_dir / "script_prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    # V1 accepts narration from the UI/client so no paid LLM key is required.
    if not narration:
        return jsonify({
            "job_id": job_id,
            "status": "needs_script",
            "script_prompt": prompt,
        })

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

    return jsonify({
        "job_id": job_id,
        "status": "complete",
        "video_url": f"/api/jobs/{job_id}/final_short.mp4",
        "captions_url": f"/api/jobs/{job_id}/captions.srt",
    })


@app.get("/api/jobs/<job_id>/<path:filename>")
def job_file(job_id, filename):
    return send_from_directory(str(OUTPUTS / job_id), filename, as_attachment=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

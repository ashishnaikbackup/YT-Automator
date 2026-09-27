from flask import Flask, request, jsonify, send_from_directory
from pipeline import generate_short
import os

app = Flask(__name__, static_folder="web", static_url_path="")

@app.get("/")
def index():
    return send_from_directory("web", "index.html")

@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    duration = int(data.get("duration") or 45)
    if not topic:
        return jsonify({"error": "Enter a topic first."}), 400
    if duration not in (30, 45, 60):
        return jsonify({"error": "Duration must be 30, 45, or 60 seconds."}), 400
    try:
        result = generate_short(topic, duration)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

@app.get("/outputs/<path:filename>")
def output_file(filename):
    return send_from_directory("outputs", filename, as_attachment=False)

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=False)

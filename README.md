# YT-Automator

Local AI-assisted YouTube Shorts generator.

**Topic → Script → Voice → Free image visuals → Fast motion cuts → Captions → MP4**

The project is intentionally kept as a **portfolio/prototype project**. It does not need to stay installed on the PC; reinstall the dependencies only when you want to run it.

## Current features

- 30 / 45 / 60 second Shorts
- Local script generation through Ollama
- Energetic neural voice with Edge TTS, with a Windows Speech fallback
- Reusable/free image visuals from Openverse and Wikimedia Commons
- Vertical 1080×1920 output
- Fast image-based motion editing with zoom/pan
- Synced ASS captions
- Automatic visual-source credits
- Local Flask web interface
- MP4 output saved under `outputs/`

The current visual approach uses **still images turned into fast-moving video clips**, rather than downloading stock video footage.

## How to use it later

### 1. Install prerequisites

- Python 3.12+ recommended
- Ollama
- Git (only if cloning the repository)

The project uses `imageio-ffmpeg`, so a separate FFmpeg installation is normally not required.

### 2. Clone the repository

```bash
git clone https://github.com/ashishnaikbackup/YT-Automator.git
cd YT-Automator
```

### 3. Start Ollama and download the model

Make sure Ollama is running, then run:

```bash
ollama pull llama3.2:3b
```

The default model can be changed with the `OLLAMA_MODEL` environment variable.

### 4. Start YT-Automator

On Windows:

```text
run_local.bat
```

Or manually:

```bash
python -m pip install -r requirements.txt
python local_app.py
```

Then open `http://127.0.0.1:5000` in your browser.

### 5. Generate a Short

1. Enter a topic.
2. Select **30**, **45**, or **60 sec**.
3. Click **Generate Short**.
4. Wait for script → voice → visuals → captions → render.
5. Preview the MP4 and save it from the browser.

Example topic:

> 3 free AI tools engineering students should know

## Important notes

- Internet is required for Edge TTS and online visual retrieval.
- If Edge TTS is unavailable, the pipeline can fall back to a Windows voice.
- Visuals are filtered toward reusable licenses and a `visual_credits.txt` file is created for each generated job.
- Generation can fail if Ollama is not running, the selected model is missing, or free visual APIs are unavailable.
- Review scripts, sources, captions, and the final video before publishing.

## Project structure

```text
YT-Automator/
├── local_app.py            # Flask local web server
├── pipeline.py             # Generation pipeline
├── run_local.bat           # Windows launcher
├── requirements.txt        # Python dependencies
├── upgrade_fast_pacing.py  # Development/upgrade helper
├── web/
│   └── index.html          # Local UI
└── outputs/                # Generated Shorts (ignored by Git)
```

## Roadmap

### V1 — Prompt to Short
- [x] Topic input
- [x] Script generation
- [x] Voice generation
- [x] Free visual retrieval
- [x] Captions
- [x] Vertical rendering

### V2 — Research
- [ ] Source-aware research before scripting
- [ ] Better fact-checking workflow
- [ ] Topic/source panel in the UI

### V3 — Trend discovery
- [ ] Discover candidate topics
- [ ] Human approval before generation

### V4 — Batch automation
- [ ] Generate multiple Shorts
- [ ] Queue jobs
- [ ] Retry failed stages

### V5 — Publishing
- [ ] Title/description/hashtags
- [ ] YouTube API integration
- [ ] Private/unlisted test upload before public publishing

## Principle

Build small, test every stage, and prefer free/local components before adding paid APIs.

## Author

Ashish Naik — [GitHub](https://github.com/ashishnaikbackup)

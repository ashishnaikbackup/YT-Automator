# YT-Automator

AI-assisted YouTube Shorts automation pipeline.

## 🌐 Live web app

**Live app:** https://yt-automator.onrender.com

The web app is deployed from this repository. The same repo contains the frontend and Python backend.

## What it does

`Prompt → Research → Script → Voice → Captions → Render`

The project also includes foundations for:

`Trending topics → Research → Script → Video`

## ₹0 / free-first design

This project is designed so the core workflow can be run without paid API subscriptions.

- **Research:** public RSS/news sources; no API key required.
- **Script:** local Ollama model support.
- **Voice:** Edge TTS support.
- **Captions:** generated locally.
- **Rendering:** MoviePy/FFmpeg locally.
- **Web UI:** Flask.

Free cloud providers can change quotas or availability. The project therefore does not claim unlimited free cloud AI. For a genuinely ₹0 setup, run the AI model locally with Ollama and render locally.

### Local setup

Install Python 3.11+ and FFmpeg, then:

```bash
pip install -r requirements.txt
```

Install Ollama and pull a small model, for example:

```bash
ollama pull llama3.2:3b
```

Start the app:

```bash
set LLM_PROVIDER=ollama
python api.py
```

Open `http://127.0.0.1:5000`.

## Content direction

Initial channel direction: **AI + technology + useful tools for students/young creators**.

Examples:
- AI tools students should know
- New AI features and launches
- Free productivity/coding tools
- Python and programming tips
- Tech explained in 30–60 seconds
- Interesting engineering/VLSI technology

Research and source attribution should be part of the workflow before publishing. Do not automatically publish unverified claims.

## Roadmap

### V1 — Prompt to Short
- Web prompt UI
- Script prompt
- Voice
- Captions
- Vertical MP4 rendering

### V2 — Research + local AI
- Recent news/RSS research
- Research-aware script prompts
- Local Ollama script generation
- Trend discovery foundation

### V3 — Visual scenes
- Scene splitting
- Visual plans
- Free/generated assets
- Animated captions and transitions

### V4 — Automation
- Automatic topic selection
- Batch generation
- Queue/retry handling
- Scheduled generation

### V5 — Publishing
- Title/description/hashtags
- Thumbnail
- YouTube API integration
- Private/unlisted approval workflow

## Project status

**Core prototype:** built.

**Important:** the hosted free web app is a demo/deployment surface. For a truly ₹0 end-to-end AI generation workflow, use the local setup so model inference and rendering happen on your own computer.

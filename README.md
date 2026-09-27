# YT-Automator

AI-assisted YouTube Shorts automation pipeline.

## 🌐 Live web app

**Live app:** https://yt-automator.onrender.com

The web app is deployed from this repository's `v1-prompt-to-short` branch. The same repo contains the frontend and Python backend; there is no separate codebase for the hosted page.

## V1: local and hosted web app

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start locally:

```bash
python api.py
```

Then open `http://127.0.0.1:5000`.

The hosted app is intended to provide the same web interface through Render. The current V1 can create a generation request and the backend can render a vertical MP4 after narration is supplied. The current V1 does not require a paid LLM key.

## Goal

Turn a simple prompt—or eventually an automatic topic trigger—into a finished vertical Short:

`Topic → Research → Script → Voice → Visuals → Captions → Render`

Future automation:

`Trending topics → Research → Fact check → Script → Voice → Visuals → Captions → Render → YouTube`

## Free-first approach

The project prioritizes free/open-source/local components. Some third-party AI APIs may have free tiers, quotas, or usage limits, so the project does **not** promise unlimited free AI generation.

## Content direction

Initial channel direction: **AI + technology + useful tools for students/young creators**.

Examples:
- AI tools students should know
- New AI features and launches
- Free productivity/coding tools
- Python and programming tips
- Tech explained in 30–60 seconds
- Interesting engineering/VLSI technology

Avoid automatically publishing unverified claims. Research and source attribution should be part of the pipeline before publishing.

## Roadmap

### V1 — Prompt to Short
- Prompt/topic input
- Script generation
- Voice generation
- Visual asset handling
- Captions
- Vertical video rendering
- Local output folder
- Local web interface
- Hosted web interface

### V2 — Research
- Web/source collection
- Source extraction
- Research summary
- Basic fact-checking workflow

### V3 — Trend discovery
- Discover candidate topics
- Rank candidates using configurable signals
- Human approval option before generation

### V4 — Batch automation
- Generate multiple Shorts
- Queue jobs
- Retry failed stages
- Structured project folders

### V5 — Publishing
- Title/description/hashtags
- Thumbnail generation
- YouTube API integration
- Private/unlisted test upload before public publishing

## Project principle

Build small, test every stage, and prefer free/local components before adding paid APIs.

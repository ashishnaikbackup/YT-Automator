# YT-Automator

AI-assisted YouTube Shorts automation pipeline.

## Goal

Turn a simple prompt—or eventually an automatic topic trigger—into a finished vertical Short:

`Topic → Research → Script → Voice → Visuals → Captions → Render`

Future automation:

`Trending topics → Research → Fact check → Script → Voice → Visuals → Captions → Render → YouTube`

## Free-first approach

The project is designed to use free/open-source tools and local processing wherever practical. Some third-party AI APIs may have free tiers, quotas, or usage limits, so the project does **not** promise unlimited free AI generation.

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
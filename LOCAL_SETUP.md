# YT-Automator — Free Local Setup

This is the ₹0-first way to run YT-Automator. Render hosts the lightweight web/API layer; your Windows PC performs local AI and video generation.

## 1. Install Ollama

Install Ollama from https://ollama.com/.

Verify it in Command Prompt:

```bat
ollama --version
```

## 2. Download a local model

For a lightweight starting point:

```bat
ollama pull llama3.2:3b
```

This downloads the model once. Generation then runs locally on your PC; Ollama does not charge per request.

## 3. Run YT-Automator

From the repository folder, double-click:

`run_local.bat`

The script creates `.venv`, installs `requirements.txt`, starts the local server, and opens the browser.

The current dependencies include Flask, requests, Pillow, MoviePy, edge-tts and python-dotenv. See `requirements.txt`.

## 4. First test

Use:

`5 free AI tools every engineering student should know`

Choose 45 seconds and Prompt mode.

Then test Auto Research with the topic box empty.

## Free-cost rule

Do not add a paid AI API key or payment method for the local workflow. Ollama runs the language model locally. Render should remain a lightweight host and must not be used to render or serve every finished MP4.

External free services can have their own limits or change their pricing/terms. Do not enable paid billing without checking first.

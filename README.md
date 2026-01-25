# LUMA - Personal Voice AI

> **Your AI companion that listens, remembers, and helps.**

LUMA is a privacy-first voice assistant powered by state-of-the-art AI. It runs locally on your machine, remembers what you tell it, and can search the web for real-time information.

<div align="center">
  <video src="https://github.com/user-attachments/assets/34e614d0-72f2-49a8-8207-bbf34c81f90b" width="100%" controls autoplay muted loop>
    Your browser does not support the video tag.
  </video>
</div>

## ✨ Features

| Feature | Description |
|---------|-------------|
|  **Voice Activated** | Say "Alexa" to start talking |
|  **Memory** | Remembers things you tell it |
|  **Web Search** | Real-time DuckDuckGo search |
|  **Private** | Runs locally, your data stays with you |
|  **Fast** | Groq-powered for instant responses |

##  Quick Start

### One-Command Install (Windows)

```powershell
irm https://mc095.github.io/LUMA/install.ps1 | iex
```

### Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/mc095/LUMA.git
cd LUMA

# 2. Install dependencies
pip install uv
uv sync

# 3. Get your Groq API key from console.groq.com/keys

# 4. Create .env file
echo "GROQ_API_KEY=your_key_here" > .env

# 5. Run LUMA
uv run python main.py
```
Once running, simply say **"Alexa"** to activate, then speak naturally:

## 📁 Project Structure

```
LUMA/
├── main.py              # Entry point
├── pyproject.toml       # Dependencies
├── luma/
│   ├── config.py        # Settings & prompts
│   ├── setup.py         # First-run setup
│   ├── core/            # Agent, memory
│   ├── db/              # SQLite database
│   └── voice/           # Audio, transcriber, TTS
└── tests/               # Unit tests
```

## 🛠️ Tech Stack

- **AI**: [Groq](https://groq.com) (llama-3.3-70b)
- **Agent**: [Agno](https://github.com/agno-ai/agno)
- **Speech**: [Moonshine](https://github.com/moonshine-ai/moonshine)
- **Wake Word**: [OpenWakeWord](https://github.com/dscripka/openWakeWord)
- **TTS**: [Edge TTS](https://github.com/rany2/edge-tts)
- **Search**: [DuckDuckGo](https://duckduckgo.com)

## 📋 Requirements

- Python 3.11+
- Microphone & Speakers
- Groq API key (free)

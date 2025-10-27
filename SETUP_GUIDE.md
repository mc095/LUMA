# 🍃 LUMA Setup Guide

## What I Built For You

### ✨ **Advanced Speech-to-Speech AI Agent**

**Framework**: Custom lightweight agentic framework (no LangChain/CrewAI overhead)
- Direct OpenAI-style function calling
- Custom tool registry pattern
- Groq/Gemini API integration

---

## 🎯 Features

1. **Speech-to-Text**: Moonshine ONNX (fast, local)
2. **Text-to-Speech**: Edge-TTS + Pygame (lightweight, high quality, NO API key needed)
3. **AI Brain**: 
   - **Primary**: Gemini Pro (with your API key) - tool calling support
   - **Fallback**: Groq Llama 3.1 70B - tool calling support
4. **Agentic Tools**:
   - Web search (DuckDuckGo)
   - URL browsing
   - File operations
   - Directory listing
   - Time queries

---

## 🔧 Installation

```bash
# Install dependencies
uv pip install edge-tts pygame google-generativeai beautifulsoup4

# Or use pip
pip install edge-tts pygame google-generativeai beautifulsoup4
```

---

## 🔑 Configuration

Your `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # Optional
```

---

## 🚀 Run

```bash
python main.py
```

---

## 🛠️ Troubleshooting

### Gemini Errors

If you see Gemini model errors, it will **automatically fall back to Groq**.

**Common Gemini issues**:
- Model name changes (using `gemini-pro` now)
- API quotas

**Solution**: Just let it fallback to Groq - works perfectly!

### TTS Issues

- **No pyttsx3**: Using Edge-TTS (Microsoft's free, high-quality TTS)
- **No playsound needed**: Using pygame for audio
- **Python 3.11+ compatible**: No audioop dependency issues

---

## 📊 What Models Are Being Used?

| Component | Model | Notes |
|-----------|-------|-------|
| STT | Moonshine Base | Local, fast, accurate |
| TTS | Edge-TTS (AriaNeural) | Free, natural voice |
| AI Brain | Gemini Pro → Groq Llama 3.1 70B | Tool calling enabled |

---

## 🎤 Voice Commands Examples

- "Search for latest AI news"
- "What's the weather in New York?" 
- "Browse example.com"
- "List files in the current directory"
- "What time is it?"
- Regular conversation works too!

---

## 🐛 Known Issues

1. **Gemini model name might change** - Will auto-fallback to Groq
2. **First TTS might be slow** - Edge-TTS downloads voice on first use
3. **Tool calling might fail** - System will respond normally

All handled gracefully with fallbacks! ✅

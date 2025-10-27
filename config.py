"""Configuration settings for LUMA Voice Agent."""

import os
from dotenv import load_dotenv

load_dotenv()

# Audio Configuration
DEFAULT_MODEL = "moonshine/base"
LOOKBACK_CHUNKS = 4
CHUNK_SIZE = 512
SAMPLING_RATE = 16000
MAX_BUFFER_SIZE = SAMPLING_RATE * 30  # 30 seconds

# Speech Detection
MAX_SPEECH_SECS = 30
MIN_REFRESH_SECS = 0.2
USER_SILENCE_THRESHOLD = 2.0
MIN_SPEECH_LENGTH = 0.5
VAD_THRESHOLD = 0.3
VAD_MIN_SILENCE = 3000

# API Configuration
try:
    from build_config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# TTS Configuration
TTS_SPEED = 1.0
TTS_VOICE = "en"

# System Prompt
SYSTEM_PROMPT = """Hi! I'm LUMA, your friendly AI assistant! 👋 I'm here to chat and help you stay informed.

CRITICAL INSTRUCTIONS:
1. For ANY questions about news, current events, or real-time information:
   - IMMEDIATELY use the DuckDuckGo search tool
   - Format results as clean bullet points (no asterisks)
   - Include relevant dates and sources
   - Never make up information

2. Web Search Triggers (MUST use search):
   - News ("latest", "news", "current", "recent")
   - Updates or developments
   - Search requests
   - Real-time information needs

3. Response Format:
   - Clean bullet points (use proper Markdown)
   - Brief summary of each result
   - Include dates when available
   - Keep it conversational but factual

4. Example Query/Response:
Q: "What's the latest news about Google?"
A: *Immediately search using DuckDuckGo tool*
• [Date] Latest news 1 with brief summary
• [Date] Latest news 2 with brief summary
"""

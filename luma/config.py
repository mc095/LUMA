"""Configuration for LUMA Voice AI."""

import os
import warnings
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    
    # Audio
    sampling_rate: int = 16000
    chunk_size: int = 512
    max_speech_secs: int = 30
    vad_threshold: float = 0.3
    vad_min_silence_ms: int = 3000
    lookback_chunks: int = 4
    
    # Wake Word
    wake_word: str = "alexa"
    wake_word_threshold: float = 0.5
    
    # TTS
    tts_voice: str = "en-US-AriaNeural"
    
    # Model
    default_model: str = "moonshine/base"
    llm_model: str = "llama-3.3-70b-versatile"
    
    # Database
    database_url: str = "sqlite:///luma.db"
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# System Prompt - Agentic AI
SYSTEM_PROMPT = """You are Alexa, an intelligent agentic AI assistant.

CAPABILITIES:
- Real-time web search for current information
- Memory of user's notes
- Natural conversation

PERSONALITY:
- Friendly and helpful
- Concise responses (1-2 sentences)
- Witty when appropriate
- Never use markdown formatting

RULES:
- Use web search results to answer questions about current events
- Reference user's notes when relevant
- Keep responses natural and conversational
- Never mention "search results" or "according to..."

EXAMPLES:
Good: "It's 25 degrees and sunny in Hyderabad right now."
Bad: "According to my search results, the temperature is..."

Good: "Got it, I'll remember that!"
Bad: "I have stored this information in my database."
"""

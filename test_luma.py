"""
Quick test script for LUMA components.
Run with: uv run python test_luma.py
"""

import os
import sys

print("=" * 50)
print("LUMA Component Test")
print("=" * 50)

# Test 1: Check imports
print("\n[1] Testing imports...")
try:
    from luma.config import settings, SYSTEM_PROMPT
    print("   ✅ Config loaded")
    print(f"   - Wake word: Hey Jia")
    print(f"   - LLM: {settings.llm_model}")
except Exception as e:
    print(f"   ❌ Config failed: {e}")

try:
    from luma.db.models import Session, Message
    from luma.db.repository import Repository
    print("   ✅ Database models loaded")
except Exception as e:
    print(f"   ❌ Database failed: {e}")

try:
    from luma.core.tools.file import read_file, list_directory, get_current_time
    print("   ✅ File tools loaded")
    print(f"   - Current time: {get_current_time()}")
except Exception as e:
    print(f"   ❌ File tools failed: {e}")

try:
    from luma.mcp.servers import get_available_servers
    servers = get_available_servers()
    print(f"   ✅ MCP servers: {', '.join(servers)}")
except Exception as e:
    print(f"   ❌ MCP failed: {e}")

try:
    from luma.ui.terminal import terminal
    print("   ✅ Terminal UI loaded")
except Exception as e:
    print(f"   ❌ Terminal UI failed: {e}")

# Test 2: Check API keys
print("\n[2] Checking API keys...")
gemini_key = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
groq_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key

if gemini_key:
    print(f"   ✅ GEMINI_API_KEY: {gemini_key[:8]}...")
else:
    print("   ⚠️ GEMINI_API_KEY not set")

if groq_key:
    print(f"   ✅ GROQ_API_KEY: {groq_key[:8]}...")
else:
    print("   ⚠️ GROQ_API_KEY not set")

if not gemini_key and not groq_key:
    print("   ❌ No API key found! Set GEMINI_API_KEY or GROQ_API_KEY in .env")

# Test 3: Database
print("\n[3] Testing database...")
try:
    repo = Repository(database_url="sqlite:///:memory:")
    session = repo.create_session(title="Test Session")
    print(f"   ✅ Created session: {session.id[:8]}...")
    
    msg = repo.add_message(session.id, "user", "Hello!")
    print(f"   ✅ Added message: {msg.content}")
    
    messages = repo.get_messages(session.id)
    print(f"   ✅ Retrieved {len(messages)} message(s)")
except Exception as e:
    print(f"   ❌ Database test failed: {e}")

# Test 4: FastAPI
print("\n[4] Testing FastAPI...")
try:
    from luma.api.main import app
    print(f"   ✅ FastAPI app loaded: {app.title} v{app.version}")
except Exception as e:
    print(f"   ❌ FastAPI failed: {e}")

# Test 5: Voice components (optional)
print("\n[5] Testing voice components...")
try:
    from luma.voice.tts import TTSHandler
    voices = TTSHandler.list_voices()
    print(f"   ✅ TTS voices available: {', '.join(voices.keys())}")
except Exception as e:
    print(f"   ⚠️ TTS: {e}")

try:
    from luma.voice.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE
    if OPENWAKEWORD_AVAILABLE:
        print("   ✅ Wake word detection available")
    else:
        print("   ⚠️ Wake word: openwakeword not installed")
except Exception as e:
    print(f"   ⚠️ Wake word: {e}")

# Summary
print("\n" + "=" * 50)
print("Test complete! Next steps:")
print("=" * 50)
print("""
1. Set API keys in .env file:
   GEMINI_API_KEY=your-key
   GROQ_API_KEY=your-key

2. Start API server:
   uv run python main.py --api
   Then visit http://localhost:8000

3. Start voice mode (requires microphone):
   uv run python main.py

4. Run unit tests:
   uv run pytest tests/ -v
""")

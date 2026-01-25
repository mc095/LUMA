"""Text-to-Speech handler with instant interruption support.

Uses Microsoft Edge TTS with chunk-based playback for instant stopping.
"""

import asyncio
import tempfile
import os
import logging
import threading
from typing import Optional, Callable

import edge_tts
import pygame

from ..config import settings

# Suppress pygame welcome
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

logger = logging.getLogger(__name__)


class TTSHandler:
    """
    TTS with instant interruption support.
    
    Uses Edge TTS for high-quality voices and pygame for playback
    with immediate stop capability.
    """
    
    VOICES = {
        'aria': 'en-US-AriaNeural',         # Fast, natural
        'jenny': 'en-US-JennyNeural',
        'guy': 'en-US-GuyNeural',
        'davis': 'en-US-DavisNeural',
    }
    
    def __init__(
        self, 
        voice: str = None,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None
    ):
        self.voice = voice or settings.tts_voice
        self.is_speaking = False
        self._stop_flag = False
        self._speak_thread: Optional[threading.Thread] = None
        self.on_start = on_start
        self.on_stop = on_stop
        
        # Initialize pygame mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except Exception as e:
            logger.warning(f"TTS init error: {e}")
    
    def speak(self, text: str):
        """Speak text with interruptible playback."""
        if not text or not text.strip():
            return
        
        self._stop_flag = False
        self.is_speaking = True
        
        if self.on_start:
            self.on_start()
        
        try:
            # Run async speak
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_speak(text))
            loop.close()
        except Exception as e:
            logger.debug(f"TTS error: {e}")
        finally:
            self.is_speaking = False
            if self.on_stop:
                self.on_stop()
    
    async def _async_speak(self, text: str):
        """Generate and play speech with stop checking."""
        tmp_path = None
        
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                tmp_path = tmp.name
            
            if self._stop_flag:
                return
            
            # Generate speech
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(tmp_path)
            
            if self._stop_flag:
                return
            
            # Play audio
            try:
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
            except Exception as e:
                logger.debug(f"Play error: {e}")
                return
            
            # Wait for playback with frequent stop checks
            while pygame.mixer.music.get_busy():
                if self._stop_flag:
                    pygame.mixer.music.stop()
                    break
                await asyncio.sleep(0.02)  # Check every 20ms for instant stop
            
        finally:
            self._cleanup(tmp_path)
    
    def _cleanup(self, path: Optional[str]):
        """Clean up temp file."""
        if not path:
            return
        try:
            if hasattr(pygame.mixer.music, 'unload'):
                pygame.mixer.music.unload()
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass
    
    def stop(self):
        """Stop speech immediately."""
        self._stop_flag = True
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_speaking = False
    
    def set_voice(self, voice: str):
        """Change voice."""
        if voice in self.VOICES:
            self.voice = self.VOICES[voice]
        else:
            self.voice = voice
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass
    
    @classmethod
    def list_voices(cls) -> dict:
        return cls.VOICES.copy()

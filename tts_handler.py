"""Text-to-Speech handler using edge-tts with pygame for playback."""

import asyncio
import tempfile
import os
import edge_tts
import pygame
import logging


class TTSHandler:
    """Handles text-to-speech using Microsoft Edge TTS (lightweight, no API key needed)."""
    
    def __init__(self):
        """Initialize TTS handler."""
        self.is_speaking = False
        self.voice = "en-US-AriaNeural"  # Natural female voice
        
        # Initialize pygame mixer for audio playback (suppress pygame logs)
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
        try:
            pygame.mixer.init()
            logging.debug("TTS engine ready")
        except Exception as e:
            logging.warning(f"TTS initialization error: {e}")
    
    def speak(self, text: str):
        """Convert text to speech using edge-tts."""
        if not text or not text.strip():
            return
        
        try:
            self.is_speaking = True
            
            # Generate speech using edge-tts
            asyncio.run(self._async_speak(text))
            
            self.is_speaking = False
        except Exception as e:
            self.is_speaking = False
            logging.warning(f"TTS Error: {e}")
    
    async def _async_speak(self, text: str):
        """Async method to generate and play speech."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Generate speech with edge-tts
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(tmp_path)
            
            # Play with pygame
            try:
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
            except Exception as e:
                logging.warning(f"Failed to play TTS audio: {e}")
                return
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
        finally:
            # Clean up temp file
            try:
                # Unload if supported
                if hasattr(pygame.mixer.music, 'unload'):
                    try:
                        pygame.mixer.music.unload()
                    except Exception:
                        pass
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass
    
    def stop(self):
        """Stop current speech."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            self.is_speaking = False
        except Exception as e:
            logging.warning(f"Error stopping TTS: {e}")
    
    def cleanup(self):
        """Clean up TTS resources."""
        try:
            self.stop()
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception as e:
            logging.warning(f"Error during TTS cleanup: {e}")

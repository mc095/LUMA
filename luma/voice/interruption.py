"""Voice interruption handler - Siri-like voice detection during TTS.

This module monitors audio input while TTS is playing and:
1. Detects when the user starts speaking
2. Plays a short acknowledgment sound ("Aha..", "Mm?")
3. Stops the current TTS playback
4. Signals the agent to listen for new input
"""

import os
import random
import threading
import queue
import logging
import tempfile
import asyncio
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
import edge_tts
import pygame

from silero_vad import load_silero_vad

from ..config import settings

logger = logging.getLogger(__name__)

# Acknowledgment phrases - Siri-like responses
ACKNOWLEDGMENT_PHRASES = [
    "Mm-hmm?",
    "Hmm?", 
    "Aha?",
    "Yes?",
    "Mm?",
]


class InterruptionHandler:
    """
    Handles voice interruption detection during TTS playback.
    
    Like Siri/Google Assistant, this monitors for user voice while
    the assistant is speaking and gracefully interrupts with
    acknowledgment sounds.
    """
    
    def __init__(
        self,
        on_interrupt: Optional[Callable] = None,
        on_ready_to_listen: Optional[Callable] = None,
        voice: str = None
    ):
        """
        Initialize interruption handler.
        
        Args:
            on_interrupt: Callback when interruption detected
            on_ready_to_listen: Callback when ready to listen after interrupt
            voice: TTS voice for acknowledgment sounds
        """
        self.on_interrupt = on_interrupt
        self.on_ready_to_listen = on_ready_to_listen
        self.voice = voice or settings.tts_voice
        
        # State
        self.is_monitoring = False
        self.is_speaking = False
        self._stop_flag = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._audio_queue: queue.Queue = queue.Queue(maxsize=10)
        
        # VAD for speech detection
        self._vad_model = None
        self._vad_threshold = 0.5  # Higher threshold to avoid noise
        
        # Pre-generated acknowledgment audio cache
        self._ack_cache: dict[str, str] = {}
        
        # Initialize
        self._init_vad()
        self._init_pygame()
    
    def _init_vad(self):
        """Initialize VAD model for voice detection."""
        try:
            self._vad_model = load_silero_vad(onnx=True)
            logger.debug("Interruption VAD initialized")
        except Exception as e:
            logger.warning(f"Failed to load VAD for interruption: {e}")
    
    def _init_pygame(self):
        """Initialize pygame mixer."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            logger.warning(f"Pygame init failed: {e}")
    
    async def pregenerate_acknowledgments(self):
        """Pre-generate acknowledgment audio files for fast playback."""
        logger.info("Pre-generating acknowledgment sounds...")
        
        for phrase in ACKNOWLEDGMENT_PHRASES:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp3',
                    prefix='ack_'
                ) as tmp:
                    communicate = edge_tts.Communicate(phrase, self.voice)
                    await communicate.save(tmp.name)
                    self._ack_cache[phrase] = tmp.name
                    logger.debug(f"Generated: '{phrase}'")
            except Exception as e:
                logger.warning(f"Failed to generate '{phrase}': {e}")
        
        logger.info(f"Generated {len(self._ack_cache)} acknowledgment sounds")
    
    def _play_acknowledgment(self):
        """Play a random acknowledgment sound."""
        if not self._ack_cache:
            # Fallback: just print
            phrase = random.choice(ACKNOWLEDGMENT_PHRASES)
            print(f"\n💬 {phrase}")
            return
        
        try:
            phrase = random.choice(list(self._ack_cache.keys()))
            audio_path = self._ack_cache[phrase]
            
            if os.path.exists(audio_path):
                # Stop current TTS first
                pygame.mixer.music.stop()
                
                # Play acknowledgment
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Wait for it to finish (short sound)
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(50)
                
                print(f"\n💬 {phrase}")
                logger.info(f"Played acknowledgment: '{phrase}'")
                
        except Exception as e:
            logger.warning(f"Failed to play acknowledgment: {e}")
            phrase = random.choice(ACKNOWLEDGMENT_PHRASES)
            print(f"\n💬 {phrase}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Audio input callback for monitoring."""
        if status:
            logger.debug(f"Audio status: {status}")
        
        try:
            if not self._audio_queue.full():
                self._audio_queue.put(indata.copy().flatten())
        except Exception:
            pass
    
    def _monitor_loop(self):
        """Background thread monitoring for voice during TTS."""
        consecutive_speech = 0
        required_consecutive = 3  # Need 3 consecutive speech frames
        
        logger.debug("Interruption monitor started")
        
        while self.is_monitoring and not self._stop_flag:
            try:
                # Get audio chunk (non-blocking with timeout)
                try:
                    chunk = self._audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Skip if not speaking (TTS not playing)
                if not self.is_speaking:
                    consecutive_speech = 0
                    continue
                
                # Run VAD
                if self._vad_model is not None:
                    try:
                        # VAD expects float32 audio
                        if chunk.dtype != np.float32:
                            chunk = chunk.astype(np.float32)
                        
                        # Get speech probability
                        speech_prob = self._vad_model(
                            chunk, 
                            settings.sampling_rate
                        ).item()
                        
                        if speech_prob > self._vad_threshold:
                            consecutive_speech += 1
                            logger.debug(f"Speech detected: {speech_prob:.2f} ({consecutive_speech})")
                            
                            if consecutive_speech >= required_consecutive:
                                # User is speaking - interrupt!
                                self._handle_interrupt()
                                consecutive_speech = 0
                        else:
                            consecutive_speech = 0
                            
                    except Exception as e:
                        logger.debug(f"VAD error: {e}")
                        
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
        
        logger.debug("Interruption monitor stopped")
    
    def _handle_interrupt(self):
        """Handle detected interruption."""
        logger.info("🎤 Voice interruption detected!")
        
        # Stop TTS
        self.is_speaking = False
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        
        # Play acknowledgment
        self._play_acknowledgment()
        
        # Callback
        if self.on_interrupt:
            self.on_interrupt()
        
        # Signal ready to listen
        if self.on_ready_to_listen:
            self.on_ready_to_listen()
    
    def start_monitoring(self):
        """Start monitoring for voice interruptions."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._stop_flag = False
        
        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Start audio stream
        try:
            self._stream = sd.InputStream(
                channels=1,
                samplerate=settings.sampling_rate,
                blocksize=512,
                callback=self._audio_callback
            )
            self._stream.start()
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            return
        
        # Start monitor thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="InterruptionMonitor"
        )
        self._monitor_thread.start()
        
        logger.debug("Interruption monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring for voice interruptions."""
        self.is_monitoring = False
        self._stop_flag = True
        
        # Stop audio stream
        if hasattr(self, '_stream') and self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        
        # Wait for thread
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        
        logger.debug("Interruption monitoring stopped")
    
    def set_speaking(self, is_speaking: bool):
        """Update speaking state."""
        self.is_speaking = is_speaking
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_monitoring()
        
        # Clean up cached audio files
        for path in self._ack_cache.values():
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass
        self._ack_cache.clear()


# Global handler instance
interruption_handler: Optional[InterruptionHandler] = None


def get_interruption_handler() -> InterruptionHandler:
    """Get or create the global interruption handler."""
    global interruption_handler
    if interruption_handler is None:
        interruption_handler = InterruptionHandler()
    return interruption_handler

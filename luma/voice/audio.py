"""Audio processing with VAD (Voice Activity Detection)."""

import queue
import asyncio
import logging
from typing import Callable, Optional
import numpy as np
import sounddevice as sd
from silero_vad import VADIterator, load_silero_vad

from ..config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Handles audio input and voice activity detection.
    
    Features:
    - Real-time audio capture
    - Voice Activity Detection (VAD)
    - Interrupt handling
    - Wake word integration
    """
    
    def __init__(
        self, 
        on_speech_detected: Callable[[np.ndarray], None],
        on_wake_word: Optional[Callable] = None
    ):
        """
        Initialize audio processor.
        
        Args:
            on_speech_detected: Callback when speech is detected
            on_wake_word: Callback when wake word is detected
        """
        self.on_speech_detected = on_speech_detected
        self.on_wake_word = on_wake_word
        
        self.running = False
        self.audio_queue: Optional[queue.Queue] = None
        self.stream: Optional[sd.InputStream] = None
        
        # Speech buffer
        self.speech_buffer = np.empty(0, dtype=np.float32)
        self.lookback_size = settings.lookback_chunks * settings.chunk_size
        self.is_speaking = False
        
        # Interrupt flag
        self.interrupt_flag = asyncio.Event()
        
        # Initialize VAD
        self.vad_model = load_silero_vad(onnx=True)
        self.vad_iterator = VADIterator(
            model=self.vad_model,
            sampling_rate=settings.sampling_rate,
            threshold=settings.vad_threshold,
            min_silence_duration_ms=settings.vad_min_silence_ms,
        )
        
        # Wake word detector (optional)
        self.wake_word_detector = None
        self.waiting_for_wake_word = True
    
    def set_wake_word_detector(self, detector):
        """Set the wake word detector."""
        self.wake_word_detector = detector
        self.waiting_for_wake_word = detector is not None
    
    def _audio_callback(self, data, frames, time, status):
        """Callback for audio input."""
        if status:
            logger.debug(f"Audio status: {status}")
        
        try:
            if self.audio_queue.full():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self.audio_queue.put((data.copy().flatten(), status))
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
    
    def start(self):
        """Start audio stream."""
        self.running = True
        self.audio_queue = queue.Queue(maxsize=5)
        
        self.stream = sd.InputStream(
            channels=1,
            samplerate=settings.sampling_rate,
            blocksize=settings.chunk_size,
            callback=self._audio_callback
        )
        self.stream.start()
        pass  # Stream started silently
    
    def process(self):
        """Process audio chunks and detect speech."""
        while self.running:
            try:
                chunk, status = self.audio_queue.get(timeout=0.1)
                
                # If waiting for wake word, check for it first
                if self.waiting_for_wake_word and self.wake_word_detector:
                    if self.wake_word_detector.detect(chunk):
                        self.waiting_for_wake_word = False
                        if self.on_wake_word:
                            self.on_wake_word()
                        # Reset VAD state
                        self._soft_reset()
                    continue
                
                # Add to speech buffer
                self.speech_buffer = np.concatenate((self.speech_buffer, chunk))
                if not self.is_speaking:
                    self.speech_buffer = self.speech_buffer[-self.lookback_size:]
                
                # VAD processing
                speech_dict = self.vad_iterator(chunk)
                
                if speech_dict:
                    if "start" in speech_dict and not self.is_speaking:
                        self.is_speaking = True
                    
                    elif "end" in speech_dict and self.is_speaking:
                        self.is_speaking = False
                        
                        if len(self.speech_buffer) > 0:
                            self.on_speech_detected(self.speech_buffer.copy())
                        
                        self.speech_buffer = np.empty(0, dtype=np.float32)
                        
                        if self.wake_word_detector:
                            self.waiting_for_wake_word = True
                
                elif self.is_speaking:
                    # Check max speech duration
                    if (len(self.speech_buffer) / settings.sampling_rate) > settings.max_speech_secs:
                        self.is_speaking = False
                        self._soft_reset()
                        
                        if len(self.speech_buffer) > 0:
                            self.on_speech_detected(self.speech_buffer.copy())
                        
                        self.speech_buffer = np.empty(0, dtype=np.float32)
                        
                        if self.wake_word_detector:
                            self.waiting_for_wake_word = True
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")
                continue
    
    def interrupt(self):
        """Interrupt current processing."""
        self.interrupt_flag.set()
        self.is_speaking = False
        self.speech_buffer = np.empty(0, dtype=np.float32)
        self._soft_reset()
    
    def reset_interrupt(self):
        """Reset interrupt flag."""
        self.interrupt_flag.clear()
    
    def _soft_reset(self):
        """Soft reset VAD iterator."""
        self.vad_iterator.triggered = False
        self.vad_iterator.temp_end = 0
        self.vad_iterator.current_sample = 0
    
    def stop(self):
        """Stop audio processing."""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self.speech_buffer = np.empty(0, dtype=np.float32)

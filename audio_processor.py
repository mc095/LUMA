"""Audio processing with VAD (Voice Activity Detection)."""

import queue
import numpy as np
import sounddevice as sd
from silero_vad import VADIterator, load_silero_vad
from config import (
    CHUNK_SIZE,
    SAMPLING_RATE,
    VAD_THRESHOLD,
    VAD_MIN_SILENCE,
    MAX_SPEECH_SECS,
    LOOKBACK_CHUNKS
)


class AudioProcessor:
    """Handles audio input and voice activity detection."""
    
    def __init__(self, on_speech_detected):
        """Initialize audio processor.
        
        Args:
            on_speech_detected: Callback function when speech is detected
        """
        self.on_speech_detected = on_speech_detected
        self.running = False
        self.audio_queue = None
        self.stream = None
        
        # Speech buffer
        self.speech_buffer = np.empty(0, dtype=np.float32)
        self.lookback_size = LOOKBACK_CHUNKS * CHUNK_SIZE
        self.is_speaking = False
        
        # Initialize VAD
        self.vad_model = load_silero_vad(onnx=True)
        self.vad_iterator = VADIterator(
            model=self.vad_model,
            sampling_rate=SAMPLING_RATE,
            threshold=VAD_THRESHOLD,
            min_silence_duration_ms=VAD_MIN_SILENCE,
        )
    
    def _audio_callback(self, data, frames, time, status):
        """Callback for audio input."""
        if status:
            print(f"Audio status: {status}")
        
        try:
            # Handle buffer overflow
            if self.audio_queue.full():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self.audio_queue.put((data.copy().flatten(), status))
        except Exception as e:
            print(f"Error in audio callback: {e}")
    
    def start(self):
        """Start audio stream."""
        self.running = True
        self.audio_queue = queue.Queue(maxsize=5)
        
        # Start audio stream
        self.stream = sd.InputStream(
            channels=1,
            samplerate=SAMPLING_RATE,
            blocksize=CHUNK_SIZE,
            callback=self._audio_callback
        )
        self.stream.start()
        print("✅ Audio stream started")
    
    def process(self):
        """Process audio chunks and detect speech."""
        while self.running:
            try:
                # Get audio chunk
                chunk, status = self.audio_queue.get(timeout=0.1)
                
                # Add to speech buffer
                self.speech_buffer = np.concatenate((self.speech_buffer, chunk))
                if not self.is_speaking:
                    self.speech_buffer = self.speech_buffer[-self.lookback_size:]
                
                # VAD processing
                speech_dict = self.vad_iterator(chunk)
                
                if speech_dict:
                    if "start" in speech_dict and not self.is_speaking:
                        self.is_speaking = True
                        print("\r🎤 Listening...", end="", flush=True)
                    
                    elif "end" in speech_dict and self.is_speaking:
                        self.is_speaking = False
                        print("\r⏳ Processing...", end="", flush=True)
                        
                        # Call callback with speech buffer
                        if len(self.speech_buffer) > 0:
                            self.on_speech_detected(self.speech_buffer.copy())
                        
                        # Reset buffer
                        self.speech_buffer = np.empty(0, dtype=np.float32)
                        print("\r✨ Ready...", end="", flush=True)
                
                elif self.is_speaking:
                    # Check max speech duration
                    if (len(self.speech_buffer) / SAMPLING_RATE) > MAX_SPEECH_SECS:
                        self.is_speaking = False
                        self._soft_reset()
                        
                        # Process speech
                        if len(self.speech_buffer) > 0:
                            self.on_speech_detected(self.speech_buffer.copy())
                        
                        self.speech_buffer = np.empty(0, dtype=np.float32)
                        print("\r✨ Ready...", end="", flush=True)
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"\n❌ Audio processing error: {e}")
                continue
    
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

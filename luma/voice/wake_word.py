"""Wake word detection - Clean version without debug output."""

import warnings
warnings.filterwarnings("ignore")

from typing import Optional, Callable
import numpy as np

try:
    from openwakeword import Model as OWWModel
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False


class WakeWordDetector:
    """Detects 'Alexa' wake word using OpenWakeWord."""
    
    def __init__(
        self, 
        threshold: float = 0.3,
        on_wake_word: Optional[Callable] = None
    ):
        self.threshold = threshold
        self.on_wake_word = on_wake_word
        self.is_active = True
        self.model = None
        
        if OPENWAKEWORD_AVAILABLE:
            try:
                self.model = OWWModel(
                    wakeword_models=["alexa"],
                    inference_framework="onnx"
                )
            except Exception:
                self.model = None
    
    def detect(self, audio_chunk: np.ndarray) -> bool:
        """Check if wake word is detected."""
        if not self.is_active or self.model is None:
            return False
        
        try:
            # Convert float32 to int16
            if audio_chunk.dtype == np.float32:
                audio_int16 = (audio_chunk * 32767).astype(np.int16)
            else:
                audio_int16 = audio_chunk.astype(np.int16)
            
            predictions = self.model.predict(audio_int16)
            
            for model_name, confidence in predictions.items():
                if confidence > self.threshold:
                    if self.on_wake_word:
                        self.on_wake_word()
                    return True
            
            return False
            
        except Exception:
            return False
    
    def reset(self):
        """Reset detector state."""
        if self.model:
            try:
                self.model.reset()
            except Exception:
                pass
    
    def activate(self):
        self.is_active = True
    
    def deactivate(self):
        self.is_active = False
    
    def cleanup(self):
        self.model = None

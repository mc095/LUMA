"""Moonshine-based speech transcription module."""

import time
import logging
from typing import Optional
import numpy as np
import torch
import warnings

from ..config import settings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# Try to import moonshine
try:
    from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
    MOONSHINE_AVAILABLE = True
except ImportError:
    MOONSHINE_AVAILABLE = False
    logger.warning("moonshine_onnx not installed. Transcription disabled.")


class Transcriber:
    """
    Handles speech-to-text transcription using Moonshine.
    
    Moonshine is a fast, lightweight ASR model that runs locally.
    """
    
    def __init__(self, model_name: str = None, sample_rate: int = 16000):
        """
        Initialize transcriber.
        
        Args:
            model_name: Moonshine model name (default: from settings)
            sample_rate: Audio sample rate (must be 16000 for Moonshine)
        """
        if sample_rate != 16000:
            raise ValueError("Moonshine only supports 16000 Hz sample rate")
        
        self.sample_rate = sample_rate
        self.model_name = model_name or settings.default_model
        
        # Statistics
        self.inference_secs = 0.0
        self.number_inferences = 0
        self.speech_secs = 0.0
        
        # Initialize model
        self.model: Optional[MoonshineOnnxModel] = None
        self.tokenizer = None
        
        if MOONSHINE_AVAILABLE:
            try:
                self.model = MoonshineOnnxModel(model_name=self.model_name)
                self.tokenizer = load_tokenizer()
                
                # Warmup
                self._warmup()
                logger.info(f"Transcription engine ready ({self.model_name})")
            except Exception as e:
                logger.error(f"Failed to initialize Moonshine: {e}")
                self.model = None
        else:
            logger.warning("Transcription not available")
    
    def _warmup(self):
        """Warmup the model with silent audio."""
        if self.model and self.tokenizer:
            dummy_audio = np.zeros(self.sample_rate, dtype=np.float32)
            self.model.generate(dummy_audio[np.newaxis, :])
    
    def __call__(self, audio: np.ndarray) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as numpy float32 array
            
        Returns:
            Transcribed text
        """
        if self.model is None or self.tokenizer is None:
            return ""
        
        self.number_inferences += 1
        self.speech_secs += len(audio) / self.sample_rate
        
        start_time = time.time()
        
        try:
            tokens = self.model.generate(audio[np.newaxis, :].astype(np.float32))
            text = self.tokenizer.decode_batch(tokens)[0]
            
            self.inference_secs += time.time() - start_time
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def get_stats(self) -> dict:
        """Get transcription statistics."""
        if self.number_inferences == 0:
            return {
                'model': self.model_name,
                'inferences': 0,
                'avg_inference_time': 0.0,
                'realtime_factor': 0.0
            }
        
        avg_time = self.inference_secs / self.number_inferences
        rtf = self.speech_secs / max(self.inference_secs, 0.001)
        
        return {
            'model': self.model_name,
            'inferences': self.number_inferences,
            'avg_inference_time': avg_time,
            'realtime_factor': rtf
        }
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.model:
                del self.model
            if self.tokenizer:
                del self.tokenizer
            torch.cuda.empty_cache()
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if transcription is available."""
        return self.model is not None

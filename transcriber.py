"""Moonshine-based transcription module."""

import time
import numpy as np
import torch
import warnings
from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
from config import DEFAULT_MODEL
import logging

# Suppress warnings
warnings.filterwarnings('ignore')


class Transcriber:
    """Handles speech-to-text transcription using Moonshine."""
    
    def __init__(self, model_name=DEFAULT_MODEL, rate=16000):
        if rate != 16000:
            raise ValueError("Moonshine supports sampling rate 16000 Hz.")
        
        self.model = MoonshineOnnxModel(model_name=model_name)
        self.rate = rate
        self.tokenizer = load_tokenizer()
        self.inference_secs = 0
        self.number_inferences = 0
        self.speech_secs = 0
        
        # Warmup model silently
        self.__call__(np.zeros(int(rate), dtype=np.float32))
        print("✅ Transcription engine ready")

    def __call__(self, speech):
        """Transcribe speech to text."""
        self.number_inferences += 1
        self.speech_secs += len(speech) / self.rate
        start_time = time.time()

        tokens = self.model.generate(speech[np.newaxis, :].astype(np.float32))
        text = self.tokenizer.decode_batch(tokens)[0]

        self.inference_secs += time.time() - start_time
        return text

    def get_stats(self):
        """Get transcription statistics."""
        if self.number_inferences == 0:
            return {
                'model': DEFAULT_MODEL,
                'inferences': 0,
                'avg_inference_time': 0,
                'realtime_factor': 0
            }
        
        avg_time = self.inference_secs / self.number_inferences
        return {
            'model': DEFAULT_MODEL,
            'inferences': self.number_inferences,
            'avg_inference_time': avg_time,
            'realtime_factor': self.speech_secs / max(self.inference_secs, 0.001)
        }

    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'model'):
                del self.model
            if hasattr(self, 'tokenizer'):
                del self.tokenizer
            torch.cuda.empty_cache()
        except Exception as e:
            logging.warning(f"Error during transcriber cleanup: {str(e)}")

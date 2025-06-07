
import os
import sys
import time
import queue
import signal
import atexit
import numpy as np
import sounddevice as sd
import torch
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream
from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
from groq import Groq
import pyttsx3
from dotenv import load_dotenv
from terminal_style import terminal


load_dotenv()

# Configuration
DEFAULT_MODEL = "moonshine/base"
LOOKBACK_CHUNKS = 4
MAX_LINE_LENGTH = 100
MAX_SPEECH_SECS = 30
MIN_REFRESH_SECS = 0.2  # Time between transcription updates during speech
USER_SILENCE_THRESHOLD = 2.0  
MIN_SPEECH_LENGTH = 0.5
VAD_THRESHOLD = 0.3  # Lower threshold to be more sensitive
VAD_MIN_SILENCE = 3000  
CHUNK_SIZE = 512
SAMPLING_RATE = 16000
MAX_BUFFER_SIZE = SAMPLING_RATE * 30  # Maximum buffer size (30 seconds)

# Initialize Groq client - (OpenAI results would be awsome too ✨)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    terminal.print_error("GROQ_API_KEY not found in environment variables")
    sys.exit(1)

client = Groq(api_key=api_key)

# Global variables
running = True
q = None
stream = None
transcriber = None
chatbot = None
tts = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully. (exit)"""
    global running
    running = False
    cleanup()

def cleanup():
    """Clean up resources. (audio picks)"""
    global stream, transcriber, chatbot, tts
    
    terminal.print_message("SYSTEM", "Cleaning up resources...")
    
    if stream is not None:
        stream.stop()
        stream.close()
    
    if transcriber is not None:
        transcriber.cleanup()
    
    if chatbot is not None:
        chatbot.cleanup()
    
    if tts is not None:
        tts.cleanup()

class Transcriber:
    def __init__(self, model_name=DEFAULT_MODEL, rate=16000):
        if rate != 16000:
            raise ValueError("Moonshine supports sampling rate 16000 Hz.")
        self.model = MoonshineOnnxModel(model_name=model_name)
        self.rate = rate
        self.tokenizer = load_tokenizer()
        self.inference_secs = 0
        self.number_inferences = 0
        self.speech_secs = 0
        self.__call__(np.zeros(int(rate), dtype=np.float32))  # Warmup model in every convo

    def __call__(self, speech):
        """Returns string containing Moonshine transcription of speech."""
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
            terminal.print_error(f"Error during cleanup: {str(e)}")

class GroqChatbot:
    def __init__(self):
        self.conversation_history = []
        self.system_prompt = """You are Luma, a friendly and helpful personal AI assistant. Your responses should be:
        - Conversational and natural, like talking to a friend
        - Concise and to the point
        - Helpful and informative
        - Empathetic and understanding
        - Professional but warm
        
        If you don't know something, be honest about it. Don't make up information.
        Keep your responses focused on being helpful while maintaining a friendly tone."""

    def get_response(self, user_input):
        """Get response from Groq API."""
        # Add user message to history (chatbot feel)
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Preparing messages for API
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        
        # Getting responses from GroqCloud (llama)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extracting and storing response
        ai_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response

    def cleanup(self):
        """Clean up resources."""
        self.conversation_history.clear()

class SimpleTTS:
    def __init__(self):
        self.engine = pyttsx3.init() 
        self.engine.setProperty('rate', 150) # voice pace
        self.engine.setProperty('volume', 1.0) # voice intensity
        
        # picking available voices
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)

    def speak(self, text):
        """Convert text to speech."""
        self.engine.say(text)
        self.engine.runAndWait()

    def cleanup(self):
        """Clean up resources."""
        self.engine.stop()

def create_input_callback(q):
    """Callback method for sounddevice InputStream."""
    def input_callback(data, frames, time, status):
        if status:
            print(f"Audio input status: {status}")
        try:
            # Handle buffer overflow by dropping old data
            if q.full():
                try:
                    q.get_nowait()  # Remove oldest item
                except queue.Empty:
                    pass
            q.put((data.copy().flatten(), status))
        except Exception as e:
            print(f"Error in input callback: {e}")
    return input_callback

def soft_reset(vad_iterator):
    """Soft resets Silero VADIterator without affecting VAD model state."""
    vad_iterator.triggered = False
    vad_iterator.temp_end = 0
    vad_iterator.current_sample = 0

def process_audio():
    """Process audio input and generate responses."""
    global running, q, transcriber, chatbot, tts
    
    speech_buffer = np.empty(0, dtype=np.float32)
    lookback_size = LOOKBACK_CHUNKS * CHUNK_SIZE
    is_speaking = False
    
    # Initialize VAD
    vad_model = load_silero_vad(onnx=True)
    vad_iterator = VADIterator(
        model=vad_model,
        sampling_rate=SAMPLING_RATE,
        threshold=VAD_THRESHOLD,
        min_silence_duration_ms=VAD_MIN_SILENCE,
    )
    
    while running:
        try:
            # Get audio chunk from queue
            chunk, status = q.get(timeout=0.1)
            if status:
                print(f"Stream status: {status}")

            # Add to speech buffer
            speech_buffer = np.concatenate((speech_buffer, chunk))
            if not is_speaking:
                speech_buffer = speech_buffer[-lookback_size:]
            
            # Check for speech using VAD
            try:
                speech_dict = vad_iterator(chunk)
                if speech_dict:
                    if "start" in speech_dict and not is_speaking:
                        is_speaking = True
                        print("\rListening...", end="", flush=True)
                    elif "end" in speech_dict and is_speaking:
                        is_speaking = False
                        print("\rProcessing...", end="", flush=True)
                        # Process the speech
                        if len(speech_buffer) > 0:
                            transcription = transcriber(speech_buffer)
                            if transcription.strip():
                                print(f"\n\n✨ You: {transcription}")
                                print("🤖 Luma is thinking...", end="", flush=True)
                                try:
                                    response = chatbot.get_response(transcription)
                                    print(f"\n\n🍃 Luma: {response}")
                                    tts.speak(response)
                                except Exception as e:
                                    print(f"\n❌ Error getting AI response: {str(e)}")
                            speech_buffer = np.empty(0, dtype=np.float32)
                            print("\rReady to listen...", end="", flush=True)
                
                elif is_speaking:
                    # Check for maximum speech duration
                    if (len(speech_buffer) / SAMPLING_RATE) > MAX_SPEECH_SECS:
                        is_speaking = False
                        soft_reset(vad_iterator)
                        print("\rProcessing...", end="", flush=True)
                        # Process the speech
                        if len(speech_buffer) > 0:
                            transcription = transcriber(speech_buffer)
                            if transcription.strip():
                                print(f"\n👤 You: {transcription}")
                                print("🤖 Luma is thinking...", end="", flush=True)
                                try:
                                    response = chatbot.get_response(transcription)
                                    print(f"\n🤖 Luma: {response}")
                                    tts.speak(response)
                                except Exception as e:
                                    print(f"\n❌ Error getting AI response: {str(e)}")
                            speech_buffer = np.empty(0, dtype=np.float32)
                            print("\rReady to listen...", end="", flush=True)
            
            except Exception as e:
                print(f"\n❌ VAD processing error: {str(e)}")
                soft_reset(vad_iterator)
                continue
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"\n❌ Error in audio processing: {str(e)}")
            break

def main():
    """Main function."""
    global running, q, stream, transcriber, chatbot, tts
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Print header
        terminal.print_header()
        
        # Initialize components
        terminal.print_status("Initializing components...", "yellow")
        transcriber = Transcriber()
        chatbot = GroqChatbot()
        tts = SimpleTTS()
        terminal.print_success("Components initialized successfully")
        
        # Set up audio stream
        terminal.print_status("Starting audio stream...", "yellow")
        q = queue.Queue(maxsize=5)
        stream = sd.InputStream(
            channels=1,
            samplerate=SAMPLING_RATE,
            blocksize=CHUNK_SIZE,
            callback=create_input_callback(q)
        )
        stream.start()
        terminal.print_success("Audio stream started")
        
        # Start audio processing
        terminal.print_status("Ready to listen...", "blue")
        process_audio()
        
    except Exception as e:
        terminal.print_error(f"Error in main: {str(e)}")
    finally:
        cleanup()
        terminal.print_success("Chatbot terminated")

if __name__ == "__main__":
    main()
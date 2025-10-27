"""
LUMA - Advanced Speech-to-Speech AI Agent
An agentic voice assistant with tool calling capabilities.
"""

import os
import sys
import signal
import atexit
import logging
from terminal_style import terminal
from config import GROQ_API_KEY
from transcriber import Transcriber
from agent import LUMAAgent
from audio_processor import AudioProcessor


# Global variables
running = True
audio_processor = None
transcriber = None
agent = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    running = False
    cleanup()
    sys.exit(0)


def cleanup():
    """Clean up all resources."""
    global audio_processor, transcriber, agent
    
    # Use debug-level logging for cleanup messages to avoid console spam
    logging.debug("Cleaning up resources...")
    
    if audio_processor is not None:
        audio_processor.cleanup()
    
    if transcriber is not None:
        transcriber.cleanup()
    
    if agent is not None:
        agent.cleanup()
    
    # No global TTS instance here; agent manages its own TTS


def on_speech_detected(speech_buffer):
    """Callback when speech is detected and ready for processing."""
    global transcriber, agent
    
    try:
        # Transcribe speech
        transcription = transcriber(speech_buffer)
        
        if transcription.strip():
            print(f"\n\n✨ You: {transcription}")
            print("🤖 LUMA is thinking...", end="", flush=True)
            
            try:
                # Get AI response with tool calling (will handle printing and TTS)
                response = agent.get_response(transcription)
                
            except Exception as e:
                print(f"\n❌ Error getting AI response: {str(e)}")
                # Let agent handle TTS for errors if available
                try:
                    if agent and hasattr(agent, 'tts') and agent.tts:
                        agent.tts.speak("I apologize, but I encountered an error processing your request.")
                except Exception:
                    pass
    
    except Exception as e:
        print(f"\n❌ Error processing speech: {str(e)}")


def main():
    """Main function."""
    global running, audio_processor, transcriber, agent
    
    # Register cleanup
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Print header
        terminal.print_header()
        # Initialize components visibly
        terminal.print_status("Initializing LUMA...", "yellow")
        # Check API keys
        if not GROQ_API_KEY:
            terminal.print_error("GROQ_API_KEY not found in environment variables")
            sys.exit(1)

        transcriber = Transcriber()
        agent = LUMAAgent()
        terminal.print_success("LUMA initialized successfully!\n")

        # Initialize audio processor
        terminal.print_status("Starting audio stream...", "yellow")
        audio_processor = AudioProcessor(on_speech_detected)
        audio_processor.start()

        terminal.print_success("Ready! Speak your command...\n")

        # Start processing audio
        audio_processor.process()
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        terminal.print_error(f"Error in main: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()
        terminal.print_success("LUMA terminated. Goodbye!")


if __name__ == "__main__":
    main()
"""
LUMA - Personal Voice AI (Terminal App)
"""

import warnings
warnings.filterwarnings("ignore")

import os
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
import signal
import atexit
import logging

from rich.console import Console

logging.disable(logging.CRITICAL)

console = Console()


def main():
    """Run LUMA."""
    from luma.setup import needs_setup, run_setup, load_env, change_settings
    
    # Check if setup needed
    if needs_setup():
        if not run_setup():
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
    else:
        load_env()
    
    from luma.config import settings
    from luma.voice.transcriber import Transcriber
    from luma.voice.audio import AudioProcessor
    from luma.voice.wake_word import WakeWordDetector
    from luma.core.agent import LUMAAgent
    from luma.db.repository import repository
    
    audio_processor = None
    transcriber = None
    agent = None
    wake_detector = None
    listening_shown = False
    
    def signal_handler(sig, frame):
        cleanup()
        console.print("\n[dim]Goodbye![/dim]")
        sys.exit(0)
    
    def cleanup():
        if audio_processor:
            audio_processor.cleanup()
        if transcriber:
            transcriber.cleanup()
        if agent:
            agent.cleanup()
    
    def on_wake_word():
        nonlocal listening_shown
        if not listening_shown:
            console.print("[cyan]*[/cyan] Listening...", end="\r")
            listening_shown = True
    
    def on_speech_detected(speech_buffer):
        nonlocal listening_shown
        listening_shown = False
        
        try:
            console.print(" " * 30, end="\r")
            
            transcription = transcriber(speech_buffer)
            
            if transcription.strip():
                console.print(f"[bold blue]You:[/bold blue] {transcription}")
                
                # Settings command
                if any(x in transcription.lower() for x in ['settings', 'change api', 'api key']):
                    change_settings()
                    console.print("[green]*[/green] Ready! Say 'Alexa' to continue")
                    return
                
                try:
                    agent.get_response(transcription, speak=True)
                except Exception:
                    console.print("[bold cyan]Alexa:[/bold cyan] Something went wrong.")
                console.print()
        except Exception:
            pass
    
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Header
        console.print()
        console.print("[bold cyan]LUMA[/bold cyan] - Personal Voice AI", justify="center")
        console.print("[dim]" + "-" * 40 + "[/dim]", justify="center")
        console.print()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            session = repository.create_session(title="Voice Session")
        
        transcriber = Transcriber()
        agent = LUMAAgent(session_id=session.id)
        wake_detector = WakeWordDetector(on_wake_word=on_wake_word)
        
        audio_processor = AudioProcessor(on_speech_detected, on_wake_word=on_wake_word)
        audio_processor.set_wake_word_detector(wake_detector)
        audio_processor.start()
        
        console.print("[green]*[/green] Ready! Say [bold]'Alexa'[/bold] to start")
        console.print("[dim]Say 'Settings' to change API key | Ctrl+C to exit[/dim]")
        console.print()
        
        audio_processor.process()
        
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
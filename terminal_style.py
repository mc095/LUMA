"""Terminal styling using Rich library."""

import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.layout import Layout
from rich.align import Align
from rich.style import Style

# Initialize Rich console
console = Console()

# ASCII Art for LUMA
LUMA_ASCII = """
                                                        ██╗     ██╗   ██╗███╗   ███╗ █████╗ 
                                                        ██║     ██║   ██║████╗ ████║██╔══██╗
                                                        ██║     ██║   ██║██╔████╔██║███████║
                                                        ██║     ██║   ██║██║╚██╔╝██║██╔══██║
                                                        ███████╗╚██████╔╝██║ ╚═╝ ██║██║  ██║
                                                        ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝
"""

class TerminalStyle:
    def __init__(self):
        self.console = Console()
        self.last_status = None
        self.last_status_time = 0
        self.typing_indicator = None
        self.live = None

    def print_header(self):
        """Print the chatbot header with ASCII art."""
        # Create welcome panel with ASCII art
        welcome_text = Text()
        welcome_text.append(LUMA_ASCII, style="bold blue")
        welcome_text.append("\n\n")
        welcome_text.append("Voice Chatbot with Groq LLaMA 3.1 and Moonshine", style="bold green")
        welcome_text.append("\n")
        welcome_text.append("Type /help for available commands", style="dim")
        
        console.print(Panel(welcome_text, border_style="blue"))

    def print_message(self, speaker, message, color="white"):
        """Print a message with minimal styling."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create message text
        message_text = Text()
        if speaker == "USER":
            message_text.append("👤 You: ", style="bold blue")
        elif speaker == "AI":
            message_text.append("🤖 Assistant: ", style="bold green")
        else:
            message_text.append(f"{speaker}: ", style="bold yellow")
        
        message_text.append(message, style=color)
        message_text.append(f" [{timestamp}]", style="dim")
        
        console.print(message_text)

    def print_status(self, message, color="yellow"):
        """Print a status message."""
        status_text = Text()
        status_text.append("● ", style=f"{color} bold")
        status_text.append(message, style=color)
        console.print(status_text, end="\r")

    def print_error(self, message):
        """Print an error message."""
        error_text = Text()
        error_text.append("❌ Error: ", style="bold red")
        error_text.append(message, style="red")
        console.print(error_text)

    def print_success(self, message):
        """Print a success message."""
        success_text = Text()
        success_text.append("✅ ", style="bold green")
        success_text.append(message, style="green")
        console.print(success_text)

    def print_stats(self, stats):
        """Print statistics in a minimal table."""
        table = Table(
            title="Session Statistics",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold blue"
        )
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Model", stats['model'])
        table.add_row("Inferences", str(stats['inferences']))
        table.add_row("Avg Inference Time", f"{stats['avg_inference_time']:.2f}s")
        table.add_row("Realtime Factor", f"{stats['realtime_factor']:.2f}x")
        
        console.print(table)

    def print_help(self):
        """Print help menu."""
        help_text = Text()
        help_text.append("Available Commands:\n\n", style="bold cyan")
        help_text.append("• ", style="bold green")
        help_text.append("/help", style="bold yellow")
        help_text.append(" - Show this help menu\n")
        help_text.append("• ", style="bold green")
        help_text.append("/stats", style="bold yellow")
        help_text.append(" - Show session statistics\n")
        help_text.append("• ", style="bold green")
        help_text.append("/exit", style="bold yellow")
        help_text.append(" - Exit the program")
        
        console.print(Panel(help_text, title="Help Menu", border_style="cyan"))

    def start_typing_indicator(self):
        """Start the typing indicator animation."""
        if self.live is None:
            self.live = Live(
                SpinnerColumn() + TextColumn("[blue]AI is thinking...[/blue]"),
                console=self.console,
                refresh_per_second=10
            )
            self.live.start()

    def stop_typing_indicator(self):
        """Stop the typing indicator animation."""
        if self.live is not None:
            self.live.stop()
            self.live = None

    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()

# Create a global instance
terminal = TerminalStyle() 
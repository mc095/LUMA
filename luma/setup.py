"""
LUMA Setup - Terminal-based using Rich.
"""

import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()


def get_luma_dir() -> Path:
    """Get LUMA config directory."""
    luma_dir = Path.home() / ".luma"
    luma_dir.mkdir(parents=True, exist_ok=True)
    return luma_dir


def get_env_path() -> Path:
    """Get .env file path."""
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env
    return get_luma_dir() / ".env"


def load_env() -> dict:
    """Load environment variables from .env."""
    env_path = get_env_path()
    config = {}
    
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
                    os.environ[key.strip()] = value.strip().strip('"\'')
    
    return config


def save_env(config: dict):
    """Save configuration to .env file."""
    env_path = get_env_path()
    
    with open(env_path, 'w') as f:
        for key, value in config.items():
            f.write(f'{key}={value}\n')
    
    for key, value in config.items():
        os.environ[key] = value


def needs_setup() -> bool:
    """Check if setup is needed."""
    load_env()
    return not os.environ.get('GROQ_API_KEY')


def run_setup() -> bool:
    """Run terminal-based setup wizard."""
    console.print()
    console.print(Panel(
        "[bold cyan]LUMA Setup[/bold cyan]\n\n"
        "Let's configure your AI assistant!",
        border_style="cyan"
    ))
    console.print()
    
    console.print("[bold]Step 1:[/bold] Groq API Key")
    console.print("[dim]Get your free API key from: https://console.groq.com/keys[/dim]")
    console.print()
    
    api_key = Prompt.ask("Enter your Groq API Key")
    
    if not api_key:
        console.print("[red]No API key provided. LUMA needs an API key to work.[/red]")
        return False
    
    save_env({"GROQ_API_KEY": api_key})
    console.print("[green]API key saved![/green]")
    console.print()
    
    return True


def change_settings():
    """Change settings interactively."""
    console.print()
    console.print("[bold cyan]LUMA Settings[/bold cyan]")
    console.print()
    
    config = load_env()
    current_key = config.get("GROQ_API_KEY", "")
    
    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "****"
        console.print(f"Current API Key: [dim]{masked}[/dim]")
    
    console.print()
    new_key = Prompt.ask("Enter new API key (or press Enter to keep current)")
    
    if new_key:
        config["GROQ_API_KEY"] = new_key
        save_env(config)
        console.print("[green]Settings saved![/green]")
    else:
        console.print("[dim]No changes made.[/dim]")
    
    console.print()


if __name__ == "__main__":
    if needs_setup():
        run_setup()
    else:
        change_settings()

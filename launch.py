"""
LUMA Launcher - Opens LUMA in a new terminal window.
"""

import subprocess
import sys
import os
from pathlib import Path


def launch():
    """Launch LUMA in a new terminal window."""
    luma_dir = Path(__file__).parent
    main_py = luma_dir / "main.py"
    
    if sys.platform == 'win32':
        # Windows: Open new cmd window
        subprocess.Popen(
            f'start "LUMA" cmd /k "cd /d {luma_dir} && uv run python main.py"',
            shell=True
        )
    elif sys.platform == 'darwin':
        # macOS: Open new Terminal window
        script = f'''
        tell application "Terminal"
            do script "cd '{luma_dir}' && uv run python main.py"
            activate
        end tell
        '''
        subprocess.Popen(['osascript', '-e', script])
    else:
        # Linux: Try common terminal emulators
        terminals = [
            ['gnome-terminal', '--', 'bash', '-c', f'cd "{luma_dir}" && uv run python main.py; exec bash'],
            ['konsole', '-e', 'bash', '-c', f'cd "{luma_dir}" && uv run python main.py; exec bash'],
            ['xterm', '-e', f'cd "{luma_dir}" && uv run python main.py; bash'],
        ]
        
        for term in terminals:
            try:
                subprocess.Popen(term)
                break
            except FileNotFoundError:
                continue


if __name__ == "__main__":
    launch()

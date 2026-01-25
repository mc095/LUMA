"""Secured file tools with path validation."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Security: Define allowed directories and blocked extensions
ALLOWED_PATHS = [
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
]

BLOCKED_EXTENSIONS = {'.env', '.pem', '.key', '.ssh', '.git', '.gpg', '.p12', '.pfx'}
BLOCKED_FILENAMES = {'id_rsa', 'id_ed25519', 'id_dsa', '.gitconfig', '.npmrc', '.pypirc'}


def validate_path(filepath: str, allow_cwd: bool = True) -> tuple[bool, str]:
    """
    Validate file path for security.
    
    Args:
        filepath: Path to validate
        allow_cwd: Whether to allow current working directory
        
    Returns:
        (is_valid, error_message)
    """
    try:
        path = Path(filepath).resolve()
        
        # Check blocked filenames
        if path.name in BLOCKED_FILENAMES:
            return False, f"Access denied: '{path.name}' is a sensitive file"
        
        # Check blocked extensions
        if path.suffix.lower() in BLOCKED_EXTENSIONS:
            return False, f"Access denied: '{path.suffix}' files are restricted"
        
        # Check if in .git, .ssh, or other hidden sensitive directories
        for part in path.parts:
            if part in {'.git', '.ssh', '.gnupg', '.aws', '.azure'}:
                return False, f"Access denied: Cannot access '{part}' directories"
        
        # Check if within allowed directories
        allowed = list(ALLOWED_PATHS)
        if allow_cwd:
            allowed.append(Path.cwd())
        
        for allowed_path in allowed:
            try:
                if path.is_relative_to(allowed_path.resolve()):
                    return True, ""
            except ValueError:
                continue
        
        return False, f"Access denied: Path must be within allowed directories"
        
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def read_file(filepath: str, max_chars: int = 5000) -> str:
    """
    Safely read contents of a file.
    
    Args:
        filepath: Path to the file to read
        max_chars: Maximum characters to return
        
    Returns:
        File contents or error message
    """
    is_valid, error = validate_path(filepath)
    if not is_valid:
        return error
    
    try:
        path = Path(filepath)
        if not path.exists():
            return f"Error: File '{filepath}' does not exist"
        
        if not path.is_file():
            return f"Error: '{filepath}' is not a file"
        
        # Check file size before reading
        size = path.stat().st_size
        if size > 1_000_000:  # 1MB limit
            return f"Error: File too large ({size} bytes). Maximum is 1MB."
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
        
        if len(content) == max_chars:
            content += f"\n... (truncated, showing first {max_chars} characters)"
        
        return content
        
    except UnicodeDecodeError:
        return f"Error: Cannot read '{filepath}' - file is not valid UTF-8 text"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_directory(path: str = ".", max_items: int = 50) -> str:
    """
    Safely list files and folders in a directory.
    
    Args:
        path: Directory path to list
        max_items: Maximum number of items to return
        
    Returns:
        Formatted directory listing or error message
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return error
    
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist"
        
        if not dir_path.is_dir():
            return f"Error: '{path}' is not a directory"
        
        items = list(dir_path.iterdir())
        
        # Separate and sort
        dirs = sorted([f"📁 {item.name}" for item in items if item.is_dir()])
        files = sorted([f"📄 {item.name}" for item in items if item.is_file()])
        
        result = []
        if dirs:
            result.append("Directories:")
            result.extend(dirs[:max_items // 2])
        if files:
            result.append("\nFiles:")
            result.extend(files[:max_items // 2])
        
        total = len(dirs) + len(files)
        if total > max_items:
            result.append(f"\n... and {total - max_items} more items")
        
        return "\n".join(result) if result else "Directory is empty"
        
    except PermissionError:
        return f"Error: Permission denied to access '{path}'"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

"""Tool definitions for LUMA using Agno Toolkit."""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from agno.tools import Toolkit


class LUMATools(Toolkit):
    """LUMA's agentic tool collection using Agno Toolkit."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="luma_tools",
            tools=[
                self.browse_url,
                self.read_file,
                self.list_directory,
                self.get_current_time
            ],
            **kwargs
        )
    
    def browse_url(self, url: str) -> str:
        """Browse and extract content from a specific URL.
        
        Args:
            url (str): The URL to browse
            
        Returns:
            str: Extracted text content from the URL
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit to first 1000 characters
            return text[:1000] + "..." if len(text) > 1000 else text
        except Exception as e:
            return f"Error browsing URL: {str(e)}"
    
    def read_file(self, filepath: str) -> str:
        """Read contents of a file from the local system.
        
        Args:
            filepath (str): Path to the file to read
            
        Returns:
            str: File contents
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            # Limit to first 2000 characters
            return content[:2000] + "..." if len(content) > 2000 else content
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def list_directory(self, path: str = ".") -> str:
        """List files and folders in a directory.
        
        Args:
            path (str): Directory path to list (defaults to current directory)
            
        Returns:
            str: List of files and directories
        """
        try:
            items = os.listdir(path)
            files = [f"📄 {item}" for item in items if os.path.isfile(os.path.join(path, item))]
            dirs = [f"📁 {item}" for item in items if os.path.isdir(os.path.join(path, item))]
            
            result = []
            if dirs:
                result.append("Directories:")
                result.extend(dirs[:10])
            if files:
                result.append("\nFiles:")
                result.extend(files[:10])
            
            return "\n".join(result) if result else "Directory is empty"
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    def get_current_time(self) -> str:
        """Get the current date and time.
        
        Returns:
            str: Current date and time
        """
        return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

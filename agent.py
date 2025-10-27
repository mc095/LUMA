"""AI Agent using Agno framework with multi-agent capabilities."""

import os
import logging
from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.groq import Groq as AgnoGroq
from agno.tools.duckduckgo import DuckDuckGoTools
from tools import LUMATools
from config import SYSTEM_PROMPT, GROQ_API_KEY
from database import MessageDatabase
from tts_handler import TTSHandler
import re

# Suppress verbose Agno logs
logging.getLogger("agno").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

# (No global DB instance here; each agent will manage a single DB instance)


class LUMAAgent:
    """Advanced AI agent using Agno framework."""
    
    def __init__(self, use_openai=False):
        """Initialize the Agno agent with tools."""
        # Get API keys
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize database
        self.db = None
        self._init_database()
        
        # Initialize tools
        tools = [LUMATools()]
        
        # Try Gemini first, fallback to Groq
        if gemini_api_key:
            try:
                # Use Gemini with web search capabilities
                self.agent = Agent(
                    model=Gemini(
                        id="gemini-2.0-flash-exp",
                        api_key=gemini_api_key
                    ),
                    description="You are an enthusiastic assistant with a flair for providing accurate information!",
                    tools=[DuckDuckGoTools()],
                    instructions=SYSTEM_PROMPT,
                    markdown=True
                )
                logging.debug(f"AI Agent initialized (Gemini 2.0 Flash) with web search capabilities")
            except Exception as e:
                logging.warning(f"Gemini failed: {e}")
                self._init_groq_agent(tools)
        else:
            self._init_groq_agent(tools)
        # Initialize TTS handler for this agent
        try:
            self.tts = TTSHandler()
        except Exception as e:
            logging.warning(f"TTS init failed: {e}")
            self.tts = None
    
    def _init_groq_agent(self, tools):
        """Initialize Groq agent with Agno."""
        self.agent = Agent(
            model=AgnoGroq(id="llama-3.3-70b-versatile"),
            description="You are an enthusiastic assistant with a flair for providing accurate information!",
            tools=[DuckDuckGoTools()],
            instructions=SYSTEM_PROMPT,
            markdown=True
        )
        logging.debug(f"AI Agent initialized (Groq Llama 3.3 70B) with web search capabilities")
    
    def get_response(self, user_input: str) -> str:
        """Get response from AI using Agno."""
        try:
            # Store user message in database
            self.db.add_message("user", user_input)

            # Add recent history to context
            recent_messages = self.db.get_recent_messages(5)  # Get last 5 messages
            context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])

            # Use Agno's run method to get response with context
            full_input = f"{context}\n\nuser: {user_input}" if context else user_input
            response = self.agent.run(full_input)

            # Determine if any tools were used (but do not print to console)
            tools_used = False
            if hasattr(response, 'messages'):
                for msg in response.messages:
                    if hasattr(msg, 'role'):
                        if msg.role == 'tool' or (hasattr(msg, 'tool_calls') and msg.tool_calls):
                            tools_used = True

            if not tools_used and ("news" in user_input.lower() or "latest" in user_input.lower() or "current" in user_input.lower()):
                # Keep as debug log only
                logging.debug("No tools were used (expected web search)")

            # Clean source parentheticals like (Source: ...) from raw content
            raw_content = getattr(response, 'content', str(response))
            raw_clean = re.sub(r"\(Source:.*?\)", "", raw_content, flags=re.IGNORECASE)

            # Format response to be more personal / conversational and remove markdown bullets
            formatted = self._format_response(raw_clean)

            # If this looks like a news query, summarize and pick one article to read (short)
            if any(w in user_input.lower() for w in ("news", "latest", "current", "update", "breaking")):
                # split into sentences and pick first 1-2 for brevity
                sent_parts = re.split(r"(?<=[.!?])\\s+", formatted)
                if len(sent_parts) > 1:
                    # take first two sentences if available
                    formatted = "Here's a quick summary: " + " ".join(sent_parts[:2]).strip()
                else:
                    formatted = "Here's a quick summary: " + formatted

            # Store assistant response in database (store formatted text)
            self.db.add_message("assistant", formatted)

            # Print response before speaking
            print(f"\n\n🍃 LUMA: {formatted}\n")

            # Speak the formatted response if TTS is available
            try:
                if self.tts:
                    # run speak async wrapper (blocking) so caller hears the TTS
                    self.tts.speak(formatted)
            except Exception as e:
                logging.warning(f"TTS speak failed: {e}")

            return formatted
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logging.error(error_msg)
            return "I apologize, but I encountered an error processing your request."
    
    
    def _init_database(self):
        """Initialize the database connection."""
        if not self.db:
            self.db = MessageDatabase()

    def _format_response(self, content: str) -> str:
        """Convert model output (possibly markdown with bullets) into a friendly, spoken-style string.

        - Removes leading bullet markers (*, -, •) and bold markers (**)
        - Joins bullet items into short sentences
        - Preserves plain paragraphs
        """
        if not content:
            return ""

        # Normalize line endings
        lines = [ln.strip() for ln in content.splitlines()]

        # Collect bullet lines
        bullets = []
        paragraphs = []
        for ln in lines:
            if not ln:
                continue
            # detect bullets (starting with *, -, •, or •)
            if ln.startswith(('* ', '- ', '• ', '*', '-')):
                # remove leading bullet markers and common markdown
                cleaned = ln.lstrip('*-• ').replace('**', '').strip()
                bullets.append(cleaned)
            else:
                # Also strip markdown bold markers
                cleaned = ln.replace('**', '').strip()
                paragraphs.append(cleaned)

        if bullets:
            # Turn bullets into conversational sentences
            sentences = []
            for b in bullets:
                # Ensure sentence ends with a period
                txt = b
                if not txt.endswith(('.', '?', '!')):
                    txt = txt.rstrip('.') + '.'
                sentences.append(txt)
            if paragraphs:
                pre = ' '.join(paragraphs)
                return f"{pre} {' '.join(sentences)}"
            return ' '.join(sentences)

        # No bullets found: return cleaned paragraphs joined by space
        return ' '.join(paragraphs)
    
    def cleanup(self):
        """Cleanup resources."""
        if self.db:
            self.db.close()
            self.db = None
    
    def clear_history(self):
        """Clear conversation history."""
        if self.db:
            self.db.clear_history()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()

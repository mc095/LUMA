"""LUMA Agentic AI with Web Search."""

import os
import warnings
warnings.filterwarnings("ignore")

import re
from typing import Optional, AsyncGenerator

from rich.console import Console

from agno.agent import Agent
from agno.models.groq import Groq as AgnoGroq

from ..config import settings, SYSTEM_PROMPT
from ..db.repository import repository
from ..voice.tts import TTSHandler
from .context import get_system_context
from .memory import get_memory

console = Console()


def web_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo search for real-time information."""
    try:
        from ddgs import DDGS
        
        search_query = ' '.join(query.lower().split())
        results = []
        ddgs = DDGS()
        
        # Use news search for current events
        if any(x in query.lower() for x in ['news', 'latest', 'recent', 'today', 'happening']):
            for r in ddgs.news(search_query, max_results=max_results):
                title = r.get('title', '')
                body = r.get('body', '')[:120]
                results.append(f"{title}: {body}")
        else:
            for r in ddgs.text(search_query, max_results=max_results):
                title = r.get('title', '')
                body = r.get('body', '')[:150]
                results.append(f"{title}: {body}")
        
        return "\n".join(results) if results else ""
    except Exception:
        return ""


class IntentHandler:
    """Handles memory intents."""
    
    def __init__(self):
        self.memory = get_memory()
    
    def handle(self, query: str) -> Optional[str]:
        q = query.lower().strip()
        
        # DELETE
        if any(x in q for x in ['forget', 'delete', 'remove']):
            if any(x in q for x in ['all notes', 'everything', 'all']):
                return self.memory.clear_all()
            
            match = re.search(r'(?:forget|delete|remove)\s+(?:the\s+)?(?:note\s+)?(?:about\s+)?(.+)', q)
            if match:
                topic = match.group(1).strip()
                for word in ['okay', 'ok', 'please', 'now']:
                    topic = topic.replace(word, '').strip()
                if topic:
                    return self.memory.delete_by_topic(topic)
        
        # REMEMBER
        if any(x in q for x in ['remember', 'save', 'note']):
            match = re.search(r'(?:remember|save|note)\s+(?:that\s+)?(.+)', q)
            if match:
                content = match.group(1).strip()
                if len(content) > 2:
                    return self.memory.add(content)
        
        # LIST NOTES
        if any(x in q for x in ['my notes', 'what do i have', 'list notes', 'show notes']):
            return self.memory.format_notes()
        
        # RECALL
        if any(x in q for x in ['what did i tell', 'what did i say', 'do you remember']):
            match = re.search(r'(?:about|regarding)\s+(.+?)[\?\.]?$', q)
            if match:
                results = self.memory.search(match.group(1).strip())
                if results:
                    return f"You told me: {results[0]['content']}"
                return "I don't have any notes about that."
            
            notes = self.memory.get_recent(3)
            if notes:
                return "Here's what I remember: " + ", ".join([n['content'] for n in notes])
            return "You haven't told me anything yet."
        
        return None


class LUMAAgent:
    """LUMA Agentic AI with memory and web search."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.agent: Optional[Agent] = None
        self.tts: Optional[TTSHandler] = None
        self.intent_handler = IntentHandler()
        
        self._init_agent()
        
        try:
            self.tts = TTSHandler()
        except Exception:
            pass
    
    def _init_agent(self):
        groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
        
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not set. Run setup first.")
        
        self.agent = Agent(
            model=AgnoGroq(
                id=settings.llm_model,
                api_key=groq_api_key
            ),
            description="Alexa - Agentic AI Assistant",
            instructions=SYSTEM_PROMPT,
            markdown=False
        )
    
    def _needs_search(self, query: str) -> bool:
        """Check if query needs web search."""
        triggers = [
            "weather", "news", "latest", "current", "today",
            "what is", "who is", "when", "where", "how",
            "tell me about", "search", "find", "look up"
        ]
        q = query.lower()
        
        # Don't search for memory operations
        if any(x in q for x in ['remember', 'forget', 'my notes', 'save']):
            return False
        
        return any(t in q for t in triggers)
    
    def _clean_response(self, content: str) -> str:
        if not content:
            return ""
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\*+', '', content)
        content = re.sub(r'\n+', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()
    
    def get_response(self, user_input: str, speak: bool = True) -> str:
        """Get AI response with memory and search."""
        
        # Handle memory intents
        intent_result = self.intent_handler.handle(user_input)
        if intent_result:
            console.print(f"[bold cyan]Alexa:[/bold cyan] {intent_result}")
            if speak and self.tts:
                self.tts.speak(intent_result)
            return intent_result
        
        # Store user message
        if self.session_id:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                repository.add_message(self.session_id, "user", user_input)
        
        # Build context
        context_parts = []
        
        # System context (time, location)
        try:
            context_parts.append(get_system_context())
        except Exception:
            pass
        
        # User's notes
        memory = get_memory()
        if memory.count() > 0:
            notes = memory.get_recent(5)
            if notes:
                notes_text = "\n".join([f"- {n['content']}" for n in notes])
                context_parts.append(f"USER'S NOTES:\n{notes_text}")
        
        # Web search if needed
        if self._needs_search(user_input):
            search_results = web_search(user_input)
            if search_results:
                context_parts.append(f"\nWEB SEARCH RESULTS:\n{search_results}")
        
        # Conversation history
        history = self._build_history()
        if history:
            context_parts.append(f"\nRECENT CONVERSATION:\n{history}")
        
        # Build prompt
        full_input = "\n\n".join(context_parts) + f"\n\nUSER: {user_input}"
        
        try:
            response = self.agent.run(full_input)
            raw = getattr(response, 'content', str(response))
            formatted = self._clean_response(raw)
            
            # Store response
            if self.session_id:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    repository.add_message(self.session_id, "assistant", formatted)
            
            console.print(f"[bold cyan]Alexa:[/bold cyan] {formatted}")
            
            if speak and self.tts:
                self.tts.speak(formatted)
            
            return formatted
            
        except Exception as e:
            msg = "Oops, something went wrong."
            console.print(f"[bold cyan]Alexa:[/bold cyan] {msg}")
            return msg
    
    async def get_response_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        response = self.get_response(user_input, speak=False)
        for word in response.split():
            yield word + " "
    
    def _build_history(self, limit: int = 5) -> str:
        if not self.session_id:
            return ""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                messages = repository.get_recent_messages(self.session_id, limit)
            if not messages:
                return ""
            return "\n".join([f"{m.role}: {m.content}" for m in messages])
        except Exception:
            return ""
    
    def set_session(self, session_id: str):
        self.session_id = session_id
    
    def cleanup(self):
        if self.tts:
            self.tts.cleanup()

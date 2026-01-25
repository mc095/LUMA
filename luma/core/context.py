"""System context provider for LUMA.

Gathers real-time information about:
- Current date/time
- User location (via IP geolocation)
- System specifications
- Weather (if API available)
"""

import os
import platform
import socket
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Cache for location (don't fetch every request)
_location_cache: Optional[dict] = None
_location_cache_time: Optional[datetime] = None


def get_current_datetime() -> str:
    """Get formatted current date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


def get_system_info() -> dict:
    """Get basic system information."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
    }


def get_location() -> dict:
    """
    Get user's approximate location via IP geolocation.
    Uses free ip-api.com service (no API key needed).
    """
    global _location_cache, _location_cache_time
    
    # Return cached location if recent (within 1 hour)
    if _location_cache and _location_cache_time:
        age = (datetime.now() - _location_cache_time).total_seconds()
        if age < 3600:  # 1 hour cache
            return _location_cache
    
    try:
        import httpx
        
        response = httpx.get(
            "http://ip-api.com/json/",
            timeout=5.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                _location_cache = {
                    "city": data.get("city", "Unknown"),
                    "region": data.get("regionName", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "timezone": data.get("timezone", "Unknown"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                }
                _location_cache_time = datetime.now()
                return _location_cache
    except Exception as e:
        logger.debug(f"Failed to get location: {e}")
    
    return {
        "city": "Unknown",
        "region": "Unknown", 
        "country": "Unknown",
        "timezone": "Unknown",
    }


def get_system_context() -> str:
    """
    Build a comprehensive system context string for the LLM.
    This provides the AI with awareness of user's environment.
    """
    # Get all info
    dt = get_current_datetime()
    location = get_location()
    system = get_system_info()
    
    context = f"""CURRENT CONTEXT:
- Date & Time: {dt}
- Location: {location['city']}, {location['region']}, {location['country']}
- Timezone: {location.get('timezone', 'Unknown')}
- System: {system['os']} ({system['os_version'][:50]}...)
- Computer: {system['hostname']}

Use this context to provide relevant, personalized responses. For weather questions, use the location above with web search."""
    
    return context


def get_weather_context(location: dict) -> str:
    """Get weather context for the given location."""
    # This would need an API key, so just provide search guidance
    city = location.get("city", "Unknown")
    return f"User is in {city}. Search for current weather in {city}."


# Pre-fetch location at module load
def _prefetch_location():
    """Background location fetch."""
    try:
        get_location()
        logger.debug("Location pre-fetched successfully")
    except Exception:
        pass


# Start pre-fetch (non-blocking)
import threading
threading.Thread(target=_prefetch_location, daemon=True).start()

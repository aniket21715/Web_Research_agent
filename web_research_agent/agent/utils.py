# agent/utils.py
import logging
import re
import time
from typing import Dict, Any, List
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s.,;:?!\'\"()-]', ' ', text)
    
    return text

def extract_main_content(html_content: str) -> str:
    """
    Extract the main content from HTML, removing boilerplate.
    This is a simplified version - in production use a library like newspaper3k or trafilatura.
    """
    # Remove script and style elements
    html_content = re.sub(r'<script[^>]*>.*?</script>', ' ', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', ' ', html_content, flags=re.DOTALL)
    
    # Remove HTML tags but keep their content
    text = re.sub(r'<[^>]*>', ' ', html_content)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def sanitize_filename(filename: str) -> str:
    """Convert a string to a valid filename."""
    # Remove invalid characters
    valid_filename = re.sub(r'[^\w\-_.]', '_', filename)
    # Truncate if too long
    return valid_filename[:100]

def rate_limit(min_time: float = 1.0):
    """Decorator to rate limit API calls."""
    last_called = {}
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            now = time.time()
            key = func.__name__
            if key in last_called:
                elapsed = now - last_called[key]
                if elapsed < min_time:
                    time.sleep(min_time - elapsed)
            
            result = func(*args, **kwargs)
            last_called[key] = time.time()
            return result
        return wrapper
    return decorator
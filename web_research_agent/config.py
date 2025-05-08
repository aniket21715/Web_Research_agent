"""
Configuration settings for the Web Research Agent.
"""

# API keys for external services
# API_KEYS = {
#     "serper": "api_key_her",  # For web search
#     # "openai": "your_openai_api_key_here",  # For content analysis (deprecated)
#     "google_ai": "api_key_her",  # For content analysis (Gemini)
# }

# config.py
import os


# API Keys
SERPER_API_KEY = "api_key_her"
GEMINI_API_KEY = "api_key_her"

# Search Settings
MAX_SEARCH_RESULTS = 5
MAX_PAGES_TO_SCRAPE = 2

# Agent Settings
LOG_LEVEL = "INFO"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

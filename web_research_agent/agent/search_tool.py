# agent/search_tool.py
import logging
import requests
import json
from typing import Dict, List, Any
from config import SERPER_API_KEY, MAX_SEARCH_RESULTS
from agent.utils import rate_limit

logger = logging.getLogger(__name__)

class SearchTool:
    """Interface for web search operations using Serper API."""
    
    def __init__(self):
        self.api_key = SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        logger.info("SearchTool initialized with Serper API")
    
    @rate_limit(min_time=1.0)
    def search(self, query: str, result_type: str = "search", num_results: int = MAX_SEARCH_RESULTS) -> Dict[str, Any]:
        """
        Perform a web search using Serper API.
        
        Args:
            query: The search query string
            result_type: Type of search (search, news, images)
            num_results: Number of results to return
            
        Returns:
            Dict containing search results
        """
        logger.info(f"Searching for: {query} (type: {result_type})")
        
        payload = {
            "q": query,
            "gl": "us",
            "hl": "en",
            "num": min(num_results, MAX_SEARCH_RESULTS)
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            results = response.json()
            
            logger.info(f"Received {len(results.get('organic', []))} search results")
            return results
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Search API error: {str(e)}")
            return {"error": str(e), "organic": []}
    
    def search_news(self, query: str, num_results: int = MAX_SEARCH_RESULTS) -> Dict[str, Any]:
        """Perform a news search."""
        logger.info(f"Searching news for: {query}")
        
        payload = {
            "q": query,
            "gl": "us",
            "hl": "en",
            "type": "news",
            "num": min(num_results, MAX_SEARCH_RESULTS)
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            results = response.json()
            
            logger.info(f"Received {len(results.get('news', []))} news results")
            return results
        
        except requests.exceptions.RequestException as e:
            logger.error(f"News search API error: {str(e)}")
            return {"error": str(e), "news": []}
    
    def extract_urls(self, search_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract URLs and metadata from search results.
        
        Returns:
            List of dicts with url, title, and snippet
        """
        urls = []
        
        # Extract from organic search results
        if "organic" in search_results:
            for result in search_results["organic"]:
                if "link" in result:
                    urls.append({
                        "url": result["link"],
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", "")
                    })
        
        # Extract from news results
        if "news" in search_results:
            for result in search_results["news"]:
                if "link" in result:
                    urls.append({
                        "url": result["link"],
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "source": result.get("source", ""),
                        "published_date": result.get("date", "")
                    })
        
        logger.info(f"Extracted {len(urls)} URLs from search results")
        return urls
# agent/analyzer.py
import logging
from typing import Dict, List, Any
import re
from datetime import datetime
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """Analyzes scraped content for relevance, reliability, and quality."""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("ContentAnalyzer initialized")
    
    def analyze_content(self, query: str, url_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze content for relevance, reliability, and extract key information.
        
        Args:
            query: Original search query
            url_data: Dict with scraped content and metadata
            
        Returns:
            Dict with analysis results
        """
        logger.info(f"Analyzing content from: {url_data['url']}")
        
        analysis = {
            "url": url_data["url"],
            "title": url_data.get("title", ""),
            "relevance_score": 0.0,
            "reliability_score": 0.0,
            "freshness_score": 0.0,
            "key_insights": [],
            "summary": "",
            "query_match": False
        }
        
        # Skip analysis if content is empty or there was an error
        if not url_data.get("success") or not url_data.get("content"):
            logger.warning(f"Skipping analysis for {url_data['url']} - no content or failed scrape")
            analysis["error"] = url_data.get("error", "No content available")
            return analysis
        
        content = url_data["content"]
        
        # Basic relevance check - do key terms from the query appear in the content?
        query_terms = re.findall(r'\w+', query.lower())
        query_term_count = sum(1 for term in query_terms if term.lower() in content.lower())
        
        # Simple relevance score based on term frequency
        if query_terms:
            relevance_ratio = query_term_count / len(query_terms)
            analysis["relevance_score"] = min(relevance_ratio * 2, 1.0)  # Scale up but cap at 1.0
        
        # Check if this content seems to answer the query
        analysis["query_match"] = analysis["relevance_score"] > 0.5
        
        # Use Gemini to analyze content
        # Truncate content if too long to avoid token limits
        max_content_length = 15000
        truncated_content = content[:max_content_length] + ("..." if len(content) > max_content_length else "")
        
        prompt = f"""
        I need you to analyze this web content in relation to the query: "{query}"
        
        Content from {url_data['url']}:
        ---
        {truncated_content}
        ---
        
        Provide a JSON response with these fields:
        1. relevance_score: A number between 0-1 indicating relevance to the query
        2. reliability_score: A number between 0-1 assessing the reliability of the information
        3. freshness_score: A number between 0-1 indicating how recent the information seems (0=outdated, 1=very current)
        4. key_insights: A list of up to 5 key facts or insights from this content relevant to the query
        5. summary: A 3-4 sentence summary of how this content relates to the query
        
        Only respond with valid JSON, no additional text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON if it's wrapped in code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            import json
            try:
                result = json.loads(response_text)
                
                # Update analysis with AI results
                analysis.update({
                    "relevance_score": result.get("relevance_score", analysis["relevance_score"]),
                    "reliability_score": result.get("reliability_score", 0.0),
                    "freshness_score": result.get("freshness_score", 0.0),
                    "key_insights": result.get("key_insights", []),
                    "summary": result.get("summary", "")
                })
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini response")
        
        except Exception as e:
            logger.error(f"Error using Gemini for content analysis: {e}")
        
        logger.info(f"Completed analysis for {url_data['url']} - Relevance: {analysis['relevance_score']:.2f}")
        return analysis
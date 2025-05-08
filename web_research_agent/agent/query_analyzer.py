# agent/query_analyzer.py
import logging
from typing import Dict, List, Any
import re
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """
    Analyzes user queries to understand intent and generate appropriate search terms.
    """
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("QueryAnalyzer initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze the user query to understand intent and formulate search strategy.
        
        Returns:
            Dict containing query analysis results:
            - intent: The perceived intent (informational, news, etc.)
            - search_terms: List of search terms to try
            - query_type: Type of query (factual, exploratory, news)
            - time_sensitivity: How time-sensitive the query is
        """
        logger.info(f"Analyzing query: {query}")
        
        # Simple rule-based detection for basic categorization
        query_lower = query.lower()
        
        # Default values
        analysis = {
            "original_query": query,
            "intent": "informational",
            "search_terms": [query],
            "query_type": "factual",
            "time_sensitivity": "low"
        }
        
        # Use Gemini to analyze the query
        prompt = f"""
        Analyze this research query: "{query}"
        
        Provide a JSON response with these fields:
        1. intent: The main intent (informational, comparative, news, how-to, etc.)
        2. search_terms: A list of 3-5 effective search terms for this query
        3. query_type: categorize as "factual", "exploratory", or "news"
        4. time_sensitivity: How time-sensitive is this query (high, medium, low)
        
        Only respond with valid JSON, no additional text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Try to parse as JSON
            import json
            try:
                # Extract JSON if it's wrapped in code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                result = json.loads(response_text)
                
                # Update analysis with AI results
                analysis.update({
                    "intent": result.get("intent", analysis["intent"]),
                    "search_terms": result.get("search_terms", analysis["search_terms"]),
                    "query_type": result.get("query_type", analysis["query_type"]),
                    "time_sensitivity": result.get("time_sensitivity", analysis["time_sensitivity"])
                })
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini response")
                # Fall back to basic analysis with some heuristics
                if re.search(r'recent|latest|news|update|current', query_lower):
                    analysis["intent"] = "news"
                    analysis["time_sensitivity"] = "high"
                    analysis["query_type"] = "news"
                elif re.search(r'how to|how do|steps|guide|tutorial', query_lower):
                    analysis["intent"] = "how-to"
                    analysis["query_type"] = "exploratory"
                elif re.search(r'compare|vs|versus|difference between', query_lower):
                    analysis["intent"] = "comparative"
                    analysis["query_type"] = "exploratory"
                
                # Generate basic search terms
                analysis["search_terms"] = [query] + [f"{query} {suffix}" for suffix in ["explained", "details", "guide"]]
        
        except Exception as e:
            logger.error(f"Error using Gemini for query analysis: {e}")
            # Fall back to basic analysis
        
        logger.info(f"Query analysis results: {analysis}")
        return analysis
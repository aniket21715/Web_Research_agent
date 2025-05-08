# agent/synthesizer.py
import logging
from typing import Dict, List, Any
import os
import json
from datetime import datetime
import google.generativeai as genai
from config import GEMINI_API_KEY
from agent.utils import sanitize_filename

logger = logging.getLogger(__name__)

class Synthesizer:
    """Synthesizes final research report from analyzed content."""
    
    def __init__(self, reports_dir="reports"):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.reports_dir = reports_dir
        
        # Ensure reports directory exists
        os.makedirs(self.reports_dir, exist_ok=True)
        
        logger.info("Synthesizer initialized")
    
    def synthesize_report(self, query: str, query_analysis: Dict[str, Any], analyzed_contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize a final research report from analyzed content.
        
        Args:
            query: Original search query
            query_analysis: Analysis of the query
            analyzed_contents: List of analyzed content from various sources
            
        Returns:
            Dict with report details and path to saved report file
        """
        logger.info(f"Synthesizing report for query: {query}")
        
        # Filter for relevant content only
        relevant_contents = [c for c in analyzed_contents if c.get("relevance_score", 0) > 0.4]
        logger.info(f"Using {len(relevant_contents)} relevant sources out of {len(analyzed_contents)} total")
        
        # Sort by relevance score
        relevant_contents.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Prepare input for Gemini
        sources_info = []
        for i, content in enumerate(relevant_contents[:10]):  # Limit to top 10 sources
            sources_info.append({
                "url": content["url"],
                "title": content.get("title", "Untitled"),
                "summary": content.get("summary", ""),
                "key_insights": content.get("key_insights", []),
                "relevance_score": content.get("relevance_score", 0),
                "reliability_score": content.get("reliability_score", 0)
            })
        
        prompt = f"""
        I need you to create a comprehensive research report answering this query: "{query}"
        
        Here are key sources I've gathered, sorted by relevance:
        
        {json.dumps(sources_info, indent=2)}
        
        Create a detailed research report that:
        1. Directly answers the original query
        2. Synthesizes information from these sources
        3. Resolves any contradictions between sources
        4. Provides nuanced analysis appropriate to the query
        5. Clearly cites sources using [1], [2], etc. with a numbered references section at the end
        6. Follows high-quality academic writing standards
        
        Format the report in Markdown with these sections:
        - Executive Summary (brief answer to the query)
        - Background
        - Key Findings
        - Analysis
        - Conclusion
        - References (numbered list of sources with URLs)
        
        Write in a professional, objective tone.
        """
        
        try:
            response = self.model.generate_content(prompt)
            report_content = response.text
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"report_{sanitize_filename(query[:30])}_{timestamp}.md"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            # Add metadata header
            metadata_header = f"""---
Query: {query}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Sources: {len(relevant_contents)}
---

"""
            report_content = metadata_header + report_content
            
            # Save the report
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            logger.info(f"Report saved to {report_path}")
            
            return {
                "query": query,
                "timestamp": timestamp,
                "report_path": report_path,
                "source_count": len(relevant_contents),
                "report_content": report_content
            }
        
        except Exception as e:
            logger.error(f"Error synthesizing report: {e}")
            return {
                "query": query,
                "error": str(e),
                "report_content": f"Error generating report: {str(e)}"
            }
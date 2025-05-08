# main.py
import os
import logging
import argparse
import time
from typing import Dict, List, Any
from datetime import datetime

from config import MAX_SEARCH_RESULTS, MAX_PAGES_TO_SCRAPE
from agent.query_analyzer import QueryAnalyzer
from agent.search_tool import SearchTool
from agent.scraper import Scraper
from agent.analyzer import ContentAnalyzer
from agent.synthesizer import Synthesizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_research_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebResearchAgent:
    """
    Web Research Agent that searches, scrapes, analyzes, and synthesizes information
    from the web based on user queries.
    """
    
    def __init__(self):
        logger.info("Initializing Web Research Agent")
        self.query_analyzer = QueryAnalyzer()
        self.search_tool = SearchTool()
        self.scraper = Scraper()
        self.content_analyzer = ContentAnalyzer()
        self.synthesizer = Synthesizer()
    
    def run_research(self, query: str) -> Dict[str, Any]:
        """
        Execute the full research pipeline on a user query.
        
        Args:
            query: The research query from the user
            
        Returns:
            Dict with research report and metadata
        """
        logger.info(f"Starting research for query: {query}")
        start_time = time.time()
        
        # Step 1: Analyze the query
        logger.info("Step 1: Analyzing query")
        query_analysis = self.query_analyzer.analyze_query(query)
        
        # Step 2: Perform web searches
        logger.info("Step 2: Performing web searches")
        search_results = []
        
        # Use the first 3 search terms from query analysis
        search_terms = query_analysis["search_terms"][:3]
        
        for term in search_terms:
            # Regular search
            results = self.search_tool.search(term)
            search_results.append(results)
            
            # If time-sensitive or news-related, also do news search
            if query_analysis["time_sensitivity"] in ["high", "medium"] or query_analysis["query_type"] == "news":
                news_results = self.search_tool.search_news(term)
                search_results.append(news_results)

        # main.py (continued)
        # Step 3: Extract and deduplicate URLs
        logger.info("Step 3: Extracting and deduplicating URLs")
        all_urls = []
        for result in search_results:
            urls = self.search_tool.extract_urls(result)
            all_urls.extend(urls)
        
        # Deduplicate URLs
        seen_urls = set()
        unique_urls = []
        for url_data in all_urls:
            if url_data["url"] not in seen_urls:
                seen_urls.add(url_data["url"])
                unique_urls.append(url_data)
        
        logger.info(f"Found {len(unique_urls)} unique URLs to process")
        
        # Sort URLs by relevance (if snippets contain query terms)
        query_terms = set(term.lower() for term in query.split())
        for url_data in unique_urls:
            snippet = url_data.get("snippet", "").lower()
            title = url_data.get("title", "").lower()
            # Simple relevance score based on query terms in snippet and title
            term_matches = sum(1 for term in query_terms if term in snippet or term in title)
            url_data["initial_relevance"] = term_matches / max(1, len(query_terms))
        
        # Sort by initial relevance
        unique_urls.sort(key=lambda x: x.get("initial_relevance", 0), reverse=True)
        
        # Limit to max pages to scrape
        urls_to_scrape = unique_urls[:MAX_PAGES_TO_SCRAPE]
        
        # Step 4: Scrape content from URLs
        logger.info(f"Step 4: Scraping content from {len(urls_to_scrape)} URLs")
        scraped_contents = []
        for url_data in urls_to_scrape:
            try:
                scraped_data = self.scraper.scrape_url(url_data["url"])
                # Merge the url_data metadata with scraped data
                scraped_data.update({
                    "snippet": url_data.get("snippet", ""),
                    "initial_relevance": url_data.get("initial_relevance", 0)
                })
                scraped_contents.append(scraped_data)
            except Exception as e:
                logger.error(f"Error scraping {url_data['url']}: {str(e)}")
        
        # Step 5: Analyze scraped content
        logger.info("Step 5: Analyzing scraped content")
        analyzed_contents = []
        for content in scraped_contents:
            if content.get("success") and content.get("content"):
                analysis = self.content_analyzer.analyze_content(query, content)
                analyzed_contents.append(analysis)
        
        # Step 6: Synthesize report
        logger.info("Step 6: Synthesizing research report")
        report = self.synthesizer.synthesize_report(query, query_analysis, analyzed_contents)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Compile results
        result = {
            "query": query,
            "execution_time": execution_time,
            "urls_found": len(unique_urls),
            "urls_scraped": len(scraped_contents),
            "urls_analyzed": len(analyzed_contents),
            "report": report
        }
        
        logger.info(f"Research completed in {execution_time:.2f} seconds")
        return result


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(description="Web Research Agent")
    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    args = parser.parse_args()
    
    agent = WebResearchAgent()
    
    if args.interactive:
        print("=== Web Research Agent ===")
        print("Enter your research query (or 'exit' to quit):")
        
        while True:
            query = input("> ")
            if query.lower() in ["exit", "quit"]:
                break
                
            if not query.strip():
                continue
                
            print(f"Researching: {query}")
            result = agent.run_research(query)
            
            if "report" in result and "report_path" in result["report"]:
                print(f"\nResearch complete! Report saved to: {result['report']['report_path']}")
                print(f"Sources found: {result['urls_found']}")
                print(f"Sources analyzed: {result['urls_analyzed']}")
                print(f"Execution time: {result['execution_time']:.2f} seconds")
                
                # Ask if user wants to see the report
                show_report = input("Would you like to see the report? (y/n): ")
                if show_report.lower() in ["y", "yes"]:
                    print("\n" + "="*50 + "\n")
                    print(result["report"]["report_content"])
                    print("\n" + "="*50)
            else:
                print("Error generating report. Check logs for details.")
    
    elif args.query:
        result = agent.run_research(args.query)
        if "report" in result and "report_path" in result["report"]:
            print(f"Research complete! Report saved to: {result['report']['report_path']}")
        else:
            print("Error generating report. Check logs for details.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()        
# #####################
Web Research Agent
# #####################
A Python-based AI agent that automatically searches the web, finds relevant information, extracts data from websites, and compiles comprehensive research reports based on user queries.
Features

Query analysis to understand user intent and formulate effective search strategies
Web search interface using Serper API
Web page scraper to extract content from URLs
Content analyzer to evaluate relevance and reliability
Report synthesizer to create comprehensive research reports

Architecture
The Web Research Agent follows a modular architecture with the following components:

Query Analyzer: Understands user intent and generates effective search terms
Search Tool: Interfaces with Serper API to perform web searches
Scraper: Extracts content from web pages
Content Analyzer: Evaluates relevance, reliability, and extracts key insights
Synthesizer: Creates final research reports from analyzed content

Flow Chart
User Query → Query Analysis → Web Search → URL Extraction
              ↓
Report Generation ← Content Synthesis ← Content Analysis ← Web Scraping
Installation

Clone this repository:

bashgit clone https://github.com/aniket21715/web-research-agent.git
cd web-research-agent

Install dependencies:

bashpip install -r requirements.txt

Set up API keys:


Usage
Command Line
bash# Run with a specific query

<!-- #####################################################################
python main.py "What are the latest advancements in quantum computing?"
    ##################################################################### -->

# Run in interactive mode
python main.py --interactive
As a Module
pythonfrom main import WebResearchAgent

agent = WebResearchAgent()
result = agent.run_research("What are the environmental impacts of electric vehicles?")
print(f"Report saved to: {result['report']['report_path']}")
Requirements

Python 3.8+
Serper API key (for web searches)
Google Gemini API key (for text analysis and synthesis)

Configuration
Configuration options are available in config.py:

MAX_SEARCH_RESULTS: Maximum number of search results to retrieve
MAX_PAGES_TO_SCRAPE: Maximum number of web pages to scrape
USER_AGENT: User agent string for web requests
LOG_LEVEL: Logging verbosity
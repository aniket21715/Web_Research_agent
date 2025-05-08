# agent/scraper.py
import logging
import requests
from typing import Dict, Any, Optional
import time
from urllib.parse import urlparse
import random
from bs4 import BeautifulSoup
import re
from agent.utils import clean_text, extract_main_content, rate_limit
from config import USER_AGENT

logger = logging.getLogger(__name__)

class Scraper:
    """Web page scraper to extract content from URLs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        logger.info("Scraper initialized")
    
    def is_allowed_by_robots(self, url: str) -> bool:
        """
        Check if specific URL is allowed by robots.txt
        """
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            path = parsed_url.path
            
            robots_url = f"{base_url}/robots.txt"
            
            response = self.session.get(robots_url, timeout=5)
            if response.status_code == 200:
                # Parse robots.txt for the path
                lines = response.text.splitlines()
                user_agent_match = False
                
                for line in lines:
                    line = line.strip()
                    
                    # Check for User-agent lines
                    if line.startswith('User-agent:'):
                        agent = line.split(':', 1)[1].strip()
                        # Match our user agent or wildcard
                        if agent == '*' or agent in self.session.headers['User-Agent']:
                            user_agent_match = True
                        else:
                            user_agent_match = False
                    
                    # Check disallow rules if we're in a matching user-agent section
                    elif user_agent_match and line.startswith('Disallow:'):
                        disallow_path = line.split(':', 1)[1].strip()
                        if disallow_path and path.startswith(disallow_path):
                            return False
            
            # If we didn't hit a disallow rule, it's allowed
            return True
        
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Assume allowed if check fails
    
    @rate_limit(min_time=2.0)
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict with scraped content, metadata, and status
        """
        logger.info(f"Scraping URL: {url}")
        
        result = {
            "url": url,
            "success": False,
            "content": "",
            "html": "",
            "title": "",
            "metadata": {},
            "error": None
        }
        
        # Check if allowed by robots.txt
        if not self.is_allowed_by_robots(url):
            logger.warning(f"URL not allowed by robots.txt: {url}")
            result["error"] = "URL not allowed by robots.txt"
            return result
        
        try:
            # Add random delay to be respectful
            time.sleep(random.uniform(1.0, 3.0))
            
            # Fetch the page
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Store the HTML
            result["html"] = response.text
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            result["title"] = title_tag.text.strip() if title_tag else ""
            
            # Extract metadata
            result["metadata"] = self._extract_metadata(soup)
            
            # Extract main content
            article_content = self._extract_article_content(soup)
            if article_content:
                result["content"] = clean_text(article_content)
            else:
                # Fall back to simple extraction
                main_content = extract_main_content(response.text)
                result["content"] = clean_text(main_content)
            
            result["success"] = True
            logger.info(f"Successfully scraped {url}, content length: {len(result['content'])}")
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from page."""
        metadata = {}
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                metadata[meta.get('name')] = meta.get('content', '')
            elif meta.get('property'):
                metadata[meta.get('property')] = meta.get('content', '')
        
        # Try to get publication date
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # MM-DD-YYYY or DD-MM-YYYY
        ]
        
        # Look for dates in specific elements or attributes
        for pattern in date_patterns:
            date_elements = soup.find_all(string=re.compile(pattern))
            if date_elements:
                match = re.search(pattern, date_elements[0])
                if match:
                    metadata['detected_date'] = match.group(1)
                    break
        
        return metadata
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content from page."""
        # Try common article container elements
        main_content = ""
        
        # Try article or main element
        article = soup.find('article') or soup.find('main')
        if article:
            main_content = article.get_text(separator=' ', strip=True)
        
        # If that fails, try content-specific IDs or classes
        if not main_content:
            for content_id in ['content', 'main-content', 'article-content', 'post-content']:
                content_elem = soup.find(id=re.compile(content_id, re.I))
                if content_elem:
                    main_content = content_elem.get_text(separator=' ', strip=True)
                    break
        
        # Try common content classes
        if not main_content:
            for content_class in ['content', 'article', 'post', 'entry']:
                content_elems = soup.find_all(class_=re.compile(content_class, re.I))
                if content_elems:
                    # Use the largest content block
                    largest_elem = max(content_elems, key=lambda x: len(x.get_text()), default=None)
                    if largest_elem:
                        main_content = largest_elem.get_text(separator=' ', strip=True)
                        break
        
        return main_content
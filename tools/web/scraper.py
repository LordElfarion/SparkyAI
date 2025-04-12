import logging
import aiohttp
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class WebScraper:
    """
    Web scraper for extracting information from websites
    """
    
    def __init__(self):
        self.session = None
    
    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def scrape_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a web page and extract useful information
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with extracted information if successful, None otherwise
        """
        try:
            # Get a session
            session = await self.ensure_session()
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract basic information
                    title = self._extract_title(soup)
                    text_content = self._extract_text(soup)
                    links = self._extract_links(soup, url)
                    metadata = self._extract_metadata(soup)
                    
                    return {
                        "url": url,
                        "title": title,
                        "content": text_content,
                        "links": links,
                        "metadata": metadata
                    }
                else:
                    logger.warning(f"Failed to scrape URL {url}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Scraping error for {url}: {str(e)}")
            return None
    
    async def extract_specific_content(self, url: str, selector: str) -> Optional[str]:
        """
        Extract specific content from a web page using a CSS selector
        
        Args:
            url: URL to scrape
            selector: CSS selector for content extraction
            
        Returns:
            Extracted content if successful, None otherwise
        """
        try:
            # Get a session
            session = await self.ensure_session()
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract content using selector
                    elements = soup.select(selector)
                    if elements:
                        # Return combined text of all matching elements
                        return '\n'.join(element.get_text(strip=True) for element in elements)
                    else:
                        logger.warning(f"No elements matching selector '{selector}' found on {url}")
                        return None
                else:
                    logger.warning(f"Failed to access URL {url}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Specific content extraction error for {url}: {str(e)}")
            return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
            
        return "No title found"
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from the page"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True)
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Only include http(s) URLs
            if absolute_url.startswith(('http://', 'https://')):
                links.append({
                    "url": absolute_url,
                    "text": text or "[No link text]"
                })
        
        return links
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from the page"""
        metadata = {}
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            
            if name and content:
                metadata[name] = content
        
        return metadata
import logging
import aiohttp
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class WebSearch:
    """
    Web search tool for finding information online
    """
    
    def __init__(self, notify_callback: Callable = None):
        self.notify_callback = notify_callback
        self.session = None
    
    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search_web(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search the web for information
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Get a session
            session = await self.ensure_session()
            
            # Encode query for URL
            encoded_query = quote_plus(query)
            
            # Attempt to use multiple search engines
            search_urls = [
                f"https://www.google.com/search?q={encoded_query}",
                f"https://www.bing.com/search?q={encoded_query}",
            ]
            
            results = []
            
            # Try search engines until we get results
            for search_url in search_urls:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parse search results
                        results = self._parse_search_results(html, num_results)
                        
                        # If we have results, stop trying search engines
                        if results:
                            break
            
            # Notify if callback is available
            if self.notify_callback:
                await self.notify_callback("search_results", {
                    "query": query,
                    "results": results
                })
                
            return results
                
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return []
    
    async def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape the content of a URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Content of the URL if successful, None otherwise
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
                else:
                    logger.warning(f"Failed to scrape URL {url}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            return None
    
    async def execute(self, input_data: str) -> str:
        """Main execution method for the tool"""
        try:
            # Parse the input as JSON if possible
            try:
                data = json.loads(input_data)
                query = data.get("query", "")
                action = data.get("action", "search")
                url = data.get("url", "")
            except json.JSONDecodeError:
                # If not JSON, assume it's a search query
                query = input_data
                action = "search"
                url = ""
            
            if action == "search":
                # Search the web
                if not query:
                    return "Please provide a search query"
                    
                await self._notify(f"Searching for: {query}")
                results = await self.search_web(query)
                
                if not results:
                    return f"No results found for '{query}'"
                    
                # Format results
                response = f"Search results for '{query}':\n\n"
                
                for i, result in enumerate(results):
                    response += f"{i+1}. {result['title']}\n"
                    response += f"   {result['url']}\n"
                    response += f"   {result['snippet']}\n\n"
                
                return response
                
            elif action == "scrape":
                # Scrape a URL
                if not url:
                    return "Please provide a URL to scrape"
                    
                await self._notify(f"Scraping URL: {url}")
                content = await self.scrape_url(url)
                
                if not content:
                    return f"Failed to scrape content from {url}"
                    
                return f"Content from {url}:\n\n{content[:2000]}..."
                
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            logger.error(f"Web search execution error: {str(e)}")
            return f"Web search error: {str(e)}"
        finally:
            # No resources to clean up
            pass
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _notify(self, message: str) -> None:
        """Send a notification via the callback if available"""
        if self.notify_callback:
            await self.notify_callback("search_notification", message)
    
    def _parse_search_results(self, html: str, num_results: int) -> List[Dict]:
        """Parse search results from HTML"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # First try Google search results pattern
        for div in soup.select('div.g')[:num_results]:
            try:
                title_element = div.select_one('h3')
                link_element = div.select_one('a')
                snippet_element = div.select_one('div.VwiC3b')
                
                if title_element and link_element and snippet_element:
                    title = title_element.text
                    url = link_element['href']
                    snippet = snippet_element.text
                    
                    # Filter out non-http URLs
                    if url.startswith('http'):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
            except Exception as e:
                logger.error(f"Error parsing search result: {str(e)}")
        
        # If no Google results, try Bing pattern
        if not results:
            for li in soup.select('li.b_algo')[:num_results]:
                try:
                    title_element = li.select_one('h2 a')
                    snippet_element = li.select_one('p')
                    
                    if title_element and snippet_element:
                        title = title_element.text
                        url = title_element['href']
                        snippet = snippet_element.text
                        
                        # Filter out non-http URLs
                        if url.startswith('http'):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                except Exception as e:
                    logger.error(f"Error parsing Bing search result: {str(e)}")
        
        return results
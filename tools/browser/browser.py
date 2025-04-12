import logging
import os
import asyncio
import base64
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class BrowserAutomation:
    """
    Browser automation tool for web interactions
    """
    
    def __init__(self, session_id: str, notify_callback = None):
        self.session_id = session_id
        self.notify_callback = notify_callback
        self.browser = None
        self.context = None
        self.page = None
        self.current_url = None
        self.history = []
        self.screenshot_dir = os.path.join("workspace", session_id, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def execute(self, input_data: str) -> str:
        """Main execution method for the tool"""
        try:
            # If input looks like a URL, navigate to it
            if input_data.startswith(("http://", "https://", "www.")):
                return await self._navigate(input_data)
            
            # Otherwise, assume it's a search query
            return await self._search(input_data)
                
        except Exception as e:
            logger.error(f"Browser automation error: {str(e)}")
            return f"Browser automation error: {str(e)}"
    
    async def _initialize_browser(self):
        """Initialize the browser if not already initialized"""
        try:
            # Import Playwright
            from playwright.async_api import async_playwright
            
            if not self.browser:
                # Start Playwright
                playwright = await async_playwright().start()
                
                # Launch browser
                self.browser = await playwright.chromium.launch(headless=True)
                
                # Create context
                self.context = await self.browser.new_context()
                
                # Create page
                self.page = await self.context.new_page()
                
                return True
            return True
        except Exception as e:
            logger.error(f"Browser initialization error: {str(e)}")
            return False
    
    async def _navigate(self, url: str) -> str:
        """Navigate to a URL"""
        try:
            # Initialize browser if needed
            if not await self._initialize_browser():
                return "Failed to initialize browser"
            
            # Add http:// prefix if needed
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            # Navigate to URL
            await self.page.goto(url, wait_until="networkidle")
            
            # Update current URL
            self.current_url = self.page.url
            self.history.append(self.current_url)
            
            # Take screenshot
            screenshot_path = await self._take_screenshot()
            
            # Extract page title
            title = await self.page.title()
            
            # Extract page content
            content = await self.page.evaluate("document.body.innerText")
            
            # Limit content length
            content = content[:500] + "..." if len(content) > 500 else content
            
            return f"**Navigated to: {title}**\n\nURL: {self.current_url}\n\n{content}\n\n[Screenshot: {screenshot_path}]"
            
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return f"Error navigating to {url}: {str(e)}"
    
    async def _search(self, query: str) -> str:
        """Perform a web search"""
        try:
            # Initialize browser if needed
            if not await self._initialize_browser():
                return "Failed to initialize browser"
            
            # Create search URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}"
            
            # Navigate to search URL
            await self.page.goto(search_url, wait_until="networkidle")
            
            # Update current URL
            self.current_url = self.page.url
            self.history.append(self.current_url)
            
            # Take screenshot
            screenshot_path = await self._take_screenshot()
            
            # Extract search results
            results = await self.page.evaluate("""() => {
                const resultElements = document.querySelectorAll('div.g');
                return Array.from(resultElements).slice(0, 5).map(el => {
                    const titleEl = el.querySelector('h3');
                    const linkEl = el.querySelector('a');
                    const snippetEl = el.querySelector('div.VwiC3b');
                    
                    return {
                        title: titleEl ? titleEl.innerText : '',
                        url: linkEl ? linkEl.href : '',
                        snippet: snippetEl ? snippetEl.innerText : ''
                    };
                });
            }""")
            
            # Format response
            response = f"**Search Results for: {query}**\n\n"
            
            for i, result in enumerate(results):
                response += f"{i+1}. **{result['title']}**\n"
                response += f"   URL: {result['url']}\n"
                response += f"   {result['snippet']}\n\n"
            
            response += f"[Screenshot: {screenshot_path}]"
            
            return response
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return f"Error searching for {query}: {str(e)}"
    
    async def _take_screenshot(self) -> str:
        """Take a screenshot of the current page"""
        try:
            # Ensure browser is initialized
            if not self.page:
                return ""
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot
            await self.page.screenshot(path=filepath, full_page=True)
            
            # Generate base64 for immediate display
            screenshot_bytes = await self.page.screenshot(full_page=True)
            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Notify with screenshot data
            if self.notify_callback:
                await self.notify_callback("screenshot", {
                    "path": filepath,
                    "data": f"data:image/png;base64,{base64_screenshot}"
                })
            
            return filepath
            
        except Exception as e:
            logger.error(f"Screenshot error: {str(e)}")
            return ""

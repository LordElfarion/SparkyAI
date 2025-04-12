from playwright.async_api import async_playwright
import asyncio
import base64
import os
from datetime import datetime
from urllib.parse import quote_plus

class BrowserAutomation:
    def __init__(self, session_id, websocket_manager):
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.browser = None
        self.page = None
        self.context = None
        self.screenshot_dir = os.path.join("workspace", session_id, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.history = []
        self.current_url = None
        
    async def start(self, user_agent=None, viewport=None):
        """Start browser instance with optional configurations"""
        self.playwright = await async_playwright().start()
        
        # Create browser instance
        self.browser = await self.playwright.chromium.launch(
            headless=True
        )
        
        # Set browser context options
        context_options = {}
        if user_agent:
            context_options["user_agent"] = user_agent
        if viewport:
            context_options["viewport"] = viewport
            
        # Create browser context
        self.context = await self.browser.new_context(**context_options)
        
        # Create page
        self.page = await self.context.new_page()
        
        # Set up page event listeners
        self.page.on("console", self._handle_console)
        self.page.on("request", self._handle_request)
        self.page.on("response", self._handle_response)
        self.page.on("dialog", self._handle_dialog)
        
        await self._notify("Browser automation started")
        return True
        
    async def navigate(self, url):
        """Navigate to a URL"""
        if not self.page:
            success = await self.start()
            if not success:
                return False
                
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            self.current_url = self.page.url
            self.history.append(self.current_url)
            
            # Take screenshot
            screenshot = await self._take_screenshot()
            
            # Get page title
            title = await self.page.title()
            
            await self._notify(f"Navigated to: {title} ({self.current_url})")
            return True
        except Exception as e:
            await self._notify(f"Navigation failed: {str(e)}")
            return False
            
    async def search(self, query):
        """Perform a search using Google"""
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        return await self.navigate(search_url)
        
    async def click(self, selector):
        """Click on an element"""
        if not self.page:
            return False
            
        try:
            # Wait for the selector to be visible
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Click the element
            await self.page.click(selector)
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            # Check if URL changed
            if self.page.url != self.current_url:
                self.current_url = self.page.url
                self.history.append(self.current_url)
                
            # Take screenshot
            screenshot = await self._take_screenshot()
            
            await self._notify(f"Clicked on element: {selector}")
            return True
        except Exception as e:
            await self._notify(f"Click failed: {str(e)}")
            return False
            
    async def type(self, selector, text, delay=50):
        """Type text into an element with optional delay"""
        if not self.page:
            return False
            
        try:
            # Wait for the selector to be visible
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Focus the element
            await self.page.focus(selector)
            
            # Clear existing content
            await self.page.fill(selector, "")
            
            # Type text with delay
            await self.page.type(selector, text, delay=delay)
            
            await self._notify(f"Typed '{text}' into {selector}")
            
            # Take screenshot
            screenshot = await self._take_screenshot()
            
            return True
        except Exception as e:
            await self._notify(f"Type failed: {str(e)}")
            return False
            
    async def extract_text(self, selector="body"):
        """Extract text content from an element"""
        if not self.page:
            return None
            
        try:
            text = await self.page.text_content(selector)
            return text.strip()
        except Exception as e:
            await self._notify(f"Text extraction failed: {str(e)}")
            return None
            
    async def extract_links(self):
        """Extract all links from the page"""
        if not self.page:
            return []
            
        try:
            links = await self.page.evaluate("""
                () => {
                    const anchors = Array.from(document.querySelectorAll('a'));
                    return anchors.map(a => {
                        return {
                            text: a.textContent.trim(),
                            href: a.href,
                            title: a.title || ""
                        };
                    });
                }
            """)
            return links
        except Exception as e:
            await self._notify(f"Link extraction failed: {str(e)}")
            return []
            
    async def _take_screenshot(self, full_page=False):
        """Take screenshot and send to client"""
        if not self.page:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        path = os.path.join(self.screenshot_dir, filename)
        
        try:
            await self.page.screenshot(path=path, full_page=full_page)
            
            # Read screenshot and encode as base64
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Send screenshot to client
            await self.websocket_manager.send_message({
                "type": "browser_screenshot",
                "data": image_data,
                "timestamp": timestamp,
                "url": self.current_url
            }, self.session_id)
            
            return filename
        except Exception as e:
            await self._notify(f"Screenshot failed: {str(e)}")
            return None
            
    async def _handle_console(self, msg):
        """Handle console messages"""
        await self._notify(f"Console: {msg.type} - {msg.text}")
        
    async def _handle_request(self, request):
        """Handle page requests"""
        # Only log main requests to reduce noise
        if request.resource_type in ["document", "xhr", "fetch"]:
            await self._notify(f"Request: {request.method} {request.url}")
        
    async def _handle_response(self, response):
        """Handle page responses"""
        # Only log main responses to reduce noise
        if response.request.resource_type in ["document", "xhr", "fetch"]:
            await self._notify(f"Response: {response.status} {response.url}")
        
    async def _handle_dialog(self, dialog):
        """Handle dialogs (alerts, confirms, prompts)"""
        message = dialog.message
        
        await self._notify(f"Dialog: {dialog.type} - {message}")
        
        # Default dialog handling
        if dialog.type == "alert":
            await dialog.accept()
        elif dialog.type == "confirm":
            await dialog.accept()  # Always accept confirm dialogs
        elif dialog.type == "prompt":
            await dialog.accept("")  # Accept with empty input
            
    async def _notify(self, message):
        """Send notification to client"""
        await self.websocket_manager.send_message({
            "type": "browser_notification",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }, self.session_id)
        
    async def close(self):
        """Close browser instance"""
        if self.page:
            await self.page.close()
            
        if self.context:
            await self.context.close()
            
        if self.browser:
            await self.browser.close()
            
        if self.playwright:
            await self.playwright.stop()
            
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        
        await self._notify("Browser automation stopped")

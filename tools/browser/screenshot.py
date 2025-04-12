import os
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable

from config.settings import settings

logger = logging.getLogger(__name__)

class ScreenshotManager:
    """
    Manages screenshots taken by the browser
    """
    
    def __init__(self, session_id: str, notify_callback: Callable = None):
        self.session_id = session_id
        self.notify_callback = notify_callback
        self.screenshot_dir = os.path.join(settings.WORKSPACE_DIR, session_id, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def save_screenshot(self, screenshot_bytes: bytes, url: str = None) -> Optional[Dict[str, Any]]:
        """
        Save a screenshot to disk and return metadata
        
        Args:
            screenshot_bytes: The raw screenshot image data
            url: Optional URL where the screenshot was taken
            
        Returns:
            Dictionary with screenshot metadata if successful, None otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Save the screenshot to disk
            with open(filepath, 'wb') as f:
                f.write(screenshot_bytes)
            
            # Convert to base64 for immediate display
            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Create metadata
            metadata = {
                "path": filepath,
                "url": url,
                "timestamp": timestamp,
                "data": f"data:image/png;base64,{base64_screenshot}"
            }
            
            # Notify if callback is available
            if self.notify_callback:
                await self.notify_callback("screenshot", metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}")
            return None
    
    def get_screenshot_path(self, timestamp: str) -> Optional[str]:
        """
        Get the path to a saved screenshot
        
        Args:
            timestamp: Screenshot timestamp in format YYYYMMDD_HHMMSS
            
        Returns:
            Path to the screenshot if it exists, None otherwise
        """
        filepath = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
        if os.path.exists(filepath):
            return filepath
        return None
    
    def list_screenshots(self) -> list:
        """
        List all screenshots for the session
        
        Returns:
            List of screenshot metadata dictionaries
        """
        screenshots = []
        
        try:
            # List all PNG files in the screenshot directory
            for filename in os.listdir(self.screenshot_dir):
                if filename.endswith('.png') and filename.startswith('screenshot_'):
                    # Extract timestamp from filename
                    timestamp = filename.replace('screenshot_', '').replace('.png', '')
                    
                    filepath = os.path.join(self.screenshot_dir, filename)
                    
                    # Create metadata
                    metadata = {
                        "path": filepath,
                        "timestamp": timestamp,
                        "size": os.path.getsize(filepath)
                    }
                    
                    screenshots.append(metadata)
            
            # Sort by timestamp (newest first)
            screenshots.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return screenshots
            
        except Exception as e:
            logger.error(f"Failed to list screenshots: {str(e)}")
            return []
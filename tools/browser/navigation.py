import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class BrowserNavigation:
    """
    Helper class for browser navigation and path tracking
    """
    
    def __init__(self):
        self.history = []
        self.current_url = None
    
    def navigate(self, url: str) -> None:
        """
        Record a navigation to a URL
        
        Args:
            url: The URL navigated to
        """
        self.current_url = url
        self.history.append(url)
    
    def get_history(self, limit: int = 10) -> List[str]:
        """
        Get navigation history
        
        Args:
            limit: Maximum number of history items to return
            
        Returns:
            List of URLs in navigation history (most recent first)
        """
        return self.history[-limit:][::-1]
    
    def can_go_back(self) -> bool:
        """
        Check if navigation can go back
        
        Returns:
            True if there is a previous URL in history, False otherwise
        """
        return len(self.history) > 1
    
    def go_back(self) -> Optional[str]:
        """
        Go back to the previous URL in history
        
        Returns:
            The previous URL if available, None otherwise
        """
        if not self.can_go_back():
            return None
        
        # Remove current URL from history
        self.history.pop()
        
        # Set current URL to previous URL
        self.current_url = self.history[-1]
        
        return self.current_url
    
    def resolve_url(self, url: str) -> str:
        """
        Resolve a relative URL against the current URL
        
        Args:
            url: The URL to resolve (may be relative)
            
        Returns:
            Absolute URL
        """
        if not url:
            return self.current_url or ""
            
        # Check if URL is already absolute
        if urlparse(url).netloc:
            return url
            
        # Resolve relative to current URL
        if self.current_url:
            return urljoin(self.current_url, url)
            
        # Cannot resolve, return as is
        return url
    
    def get_domain(self, url: Optional[str] = None) -> Optional[str]:
        """
        Get the domain of a URL
        
        Args:
            url: The URL to get the domain from (defaults to current URL)
            
        Returns:
            Domain name if available, None otherwise
        """
        try:
            target_url = url or self.current_url
            if not target_url:
                return None
                
            parsed = urlparse(target_url)
            return parsed.netloc
        except:
            return None
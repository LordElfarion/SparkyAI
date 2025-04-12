import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Log request start
        logger.info(f"Request started: {method} {url} from {client_host}")
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request completion
            logger.info(f"Request completed: {method} {url} - Status: {response.status_code} - Time: {process_time:.4f}s")
            
            return response
        except Exception as e:
            # Log exceptions
            logger.error(f"Request failed: {method} {url} - Error: {str(e)}")
            raise
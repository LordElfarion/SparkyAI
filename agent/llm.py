import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LlamaLLM:
    """Interface to Ollama LLM API"""
    
    def __init__(self, api_url=None, model_name=None):
        """Initialize the LLM connector"""
        # Try to get config values, or use defaults
        try:
            from config import OLLAMA_API_URL, OLLAMA_MODEL
            self.api_url = api_url or OLLAMA_API_URL
            self.model_name = model_name or OLLAMA_MODEL
        except ImportError:
            self.api_url = api_url or "http://localhost:11434/api/generate"
            self.model_name = model_name or "llama3"
            logger.warning("Could not import config - using default Ollama settings")
        
        logger.info(f"Initializing LLM with API URL: {self.api_url} and model: {self.model_name}")
        self.session = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=1024):
        """Generate text using Ollama API"""
        try:
            # Validate API URL
            if not self.api_url:
                raise ValueError("No API URL provided")
            
            # Construct the request payload
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_data["system"] = system_prompt
            
            logger.debug(f"Sending request to {self.api_url} with model {self.model_name}")
            
            # Get a session
            session = await self._ensure_session()
            
            # Set timeout to prevent hanging
            timeout = aiohttp.ClientTimeout(total=60)
            
            # Send the request
            async with session.post(self.api_url, json=request_data, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error: {response.status} - {error_text}")
                    return f"Error connecting to Ollama API (Status: {response.status}). Please check your server configuration."
                
                # Parse the response
                response_data = await response.json()
                logger.debug("Received response from Ollama API")
                
                # Extract the generated text
                generated_text = response_data.get("response", "")
                
                return generated_text
        
        except aiohttp.ClientConnectorError:
            logger.error(f"Cannot connect to Ollama API at {self.api_url}")
            return "Error: Cannot connect to Ollama API. Please check if Ollama is running on your server."
        
        except asyncio.TimeoutError:
            logger.error("Request to Ollama API timed out")
            return "Error: Ollama API request timed out. The server might be overloaded."
        
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error: An unexpected error occurred: {str(e)}"
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

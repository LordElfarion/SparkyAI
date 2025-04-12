import json
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)

class LlamaLLM:
    """
    Implementation of the Llama3 LLM using the Ollama API.
    """
    
    def __init__(self):
        self.api_url = settings.LLAMA_API_URL
        self.model_name = settings.LLAMA_MODEL
        self.session = None
        logger.info(f"Initializing LLM with API URL: {self.api_url} and model: {self.model_name}")
    
    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate text using Llama API"""
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
            session = await self.ensure_session()
            
            # Set timeout to prevent hanging
            timeout = aiohttp.ClientTimeout(total=60)
            
            # Send the request
            async with session.post(self.api_url, json=request_data, timeout=timeout) as response:
                if response.status == 200:
                    response_data = await response.json()
                    logger.debug("Received response from Llama API")
                    return response_data.get("response", "")
                else:
                    error_text = await response.text()
                    logger.error(f"API Error ({response.status}): {error_text}")
                    return f"Error connecting to Llama API (Status: {response.status}). Please check your server configuration."
        
        except aiohttp.ClientConnectError:
            logger.error(f"Cannot connect to Llama API at {self.api_url}")
            return "Error: Cannot connect to Llama API. Please check if Ollama is running on your server."
            
        except aiohttp.ClientTimeoutError:
            logger.error("Request to Ollama API timed out")
            return "Error: Ollama API request timed out. The server might be overloaded."
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error: An unexpected error occurred: {str(e)}"
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
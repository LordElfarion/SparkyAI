import json
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)

class OpenAILLM:
    """
    Implementation of OpenAI's LLM API as a fallback option.
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"  # Default model
        self.session = None
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. OpenAI LLM will not work.")
        else:
            logger.info(f"Initializing OpenAI LLM with model: {self.model}")
    
    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate text using OpenAI API"""
        try:
            # Validate API key
            if not self.api_key:
                raise ValueError("No OpenAI API key provided")
            
            # Construct the messages array
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add user prompt
            messages.append({"role": "user", "content": prompt})
            
            # Construct the request payload
            request_data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Get a session
            session = await self.ensure_session()
            
            # Set timeout to prevent hanging
            timeout = aiohttp.ClientTimeout(total=60)
            
            # Send the request
            async with session.post(
                self.api_url, 
                json=request_data, 
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=timeout
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    logger.debug("Received response from OpenAI API")
                    return response_data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    logger.error(f"API Error ({response.status}): {error_text}")
                    return f"Error connecting to OpenAI API (Status: {response.status}). Please check your API key and account status."
        
        except aiohttp.ClientConnectError:
            logger.error("Cannot connect to OpenAI API")
            return "Error: Cannot connect to OpenAI API. Please check your internet connection."
            
        except aiohttp.ClientTimeoutError:
            logger.error("Request to OpenAI API timed out")
            return "Error: OpenAI API request timed out. The service might be experiencing high demand."
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error: An unexpected error occurred: {str(e)}"
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
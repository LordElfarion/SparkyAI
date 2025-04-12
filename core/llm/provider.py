import logging
from typing import Union
from config.settings import settings
from core.llm.llama import LlamaLLM
from core.llm.openai import OpenAILLM

logger = logging.getLogger(__name__)

def get_llm_provider() -> Union[LlamaLLM, OpenAILLM]:
    """
    Factory function to get the appropriate LLM provider based on configuration.
    Returns an instance of either LlamaLLM or OpenAILLM.
    """
    if settings.USE_OPENAI and settings.OPENAI_API_KEY:
        logger.info("Using OpenAI as LLM provider")
        return OpenAILLM()
    else:
        logger.info("Using Llama as LLM provider")
        return LlamaLLM()
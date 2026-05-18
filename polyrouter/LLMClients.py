# File act as a interface between user defined universal call functions and llm clients specific invoke functions


# ALL the clients to which i can make calls

from abc import ABC, abstractmethod
import os
import groq
from dotenv import load_dotenv
import json
import threading
from groq import Groq
from google import genai
from google.genai import types
from polyrouter.config import (
    GROQ_MODEL, GROQ_KEY, GEMINI_MODEL, GEMINI_KEY,
    UTILS_DIR, DEBUG, IN_DEPTH_DEBUG, CEREBRAS_KEY, CEREBRAS_MODEL
)
from polyrouter.Exceptions import (
    NoAPIKeysError, NoModelMentioned, UnknownError
)
from cerebras.cloud.sdk import Cerebras

load_dotenv()
CURR_DIR = UTILS_DIR / "LLMClients.py"

class LLM(ABC):
    """
    Each LLM subclass manages its own keys and models.
    call() returns None when fully exhausted (all keys x all models tried).
    InitLLM uses this signal to switch to the next client.
    """
    @abstractmethod
    def call(self, user_input, json_mode=False):
        pass

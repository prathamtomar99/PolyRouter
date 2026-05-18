from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent

UTILS_DIR = ROOT_DIR/"Utils/"
TEST_DIR = ROOT_DIR/"Test/"


# =============================================================
# both 1 to get all debug
# Debug 1 to get major statements only
DEBUG = 1
IN_DEPTH_DEBUG = 1


# =============================================================
# API CONFIGURATIONS

# All available models in different clients

# GROQ_MODEL = ["openai/gpt-oss-120b","openai/gpt-oss-20b","llama-3.3-70b-versatile","llama-3.1-8b-instant","meta-llama/llama-4-scout-17b-16e-instruct", "qwen/qwen-3-32b", "moonshotai/kimi-k2-instruct-0905"]
# CEREBRAS_MODEL = ["llama3.1-8b", "gpt-oss-120b", "qwen-3-235b-a22b-instruct-2507", "zai-glm-4.7"]
# GEMINI_MODEL = ["gemini-2.5-flash","gemini-2.5-flash-lite"]


# All Available number of keys configurations for each client

GROQ_KEY = 6
GEMINI_KEY = 8
CEREBRAS_KEY = 6


# Best Models

GROQ_MODEL = ["openai/gpt-oss-120b","openai/gpt-oss-20b","llama-3.3-70b-versatile","llama-3.1-8b-instant"]
GEMINI_MODEL = ["gemini-2.5-flash","gemini-2.5-flash-lite"]
CEREBRAS_MODEL = ["gpt-oss-120b", "qwen-3-235b-a22b-instruct-2507"]
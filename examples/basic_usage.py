from polyrouter import LLMOrchestrator
import os
from dotenv import load_dotenv
load_dotenv()

GROQ_MODEL = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct", 
    "qwen/qwen3-32b"
]
GROQ_KEYS = [
    os.getenv("GROQ_API_KEY0"),
    os.getenv("GROQ_API_KEY1"),
    os.getenv("GROQ_API_KEY2"),
    os.getenv("GROQ_API_KEY3")
]

GEMINI_MODEL = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY0"),
    os.getenv("GEMINI_API_KEY1"),
    os.getenv("GEMINI_API_KEY2"),
    os.getenv("GEMINI_API_KEY3"),
    os.getenv("GEMINI_API_KEY4")
]

CEREBRAS_MODEL = [
    "llama3.1-8b", 
    "gpt-oss-120b", 
    "qwen-3-235b-a22b-instruct-2507", 
    "zai-glm-4.7"
]
CEREBRAS_KEYS = [
    os.getenv("CEREBRAS_API_KEY0")
]


# Test each llm with API * MODEL
llm = LLMOrchestrator(
    groq={
        "groq_models" : GROQ_MODEL,
        "groq_keys" : GROQ_KEYS,
    },
    gemini={
        "gemini_models" : GEMINI_MODEL,
        "gemini_keys" : GEMINI_KEYS,
    },
    debug=0,        # major logs
    verbose=0,      # in-depth trace
    prompt="You are a good chatbot",
    temperature=0.2,
    max_output_tokens=400,
    test_mode=1
)

# # Init a object for usage
# llm = LLMOrchestrator(
#     groq={
#         "groq_models" : GROQ_MODEL,
#         "groq_keys" : GROQ_KEYS,
#     },
#     gemini={
#         "gemini_models" : GEMINI_MODEL,
#         "gemini_keys" : GEMINI_KEYS,
#     },
#     debug=True,        # major logs
#     verbose=True,      # in-depth trace
#     prompt="You are a good chatbot",
#     temperature=0.2,
#     max_output_tokens=400,
# )


from polyrouter import LLMOrchestrator
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    filename="poly_router.log",
    level = logging.DEBUG,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",
)

# Only your library logs
logging.getLogger("polyrouter").setLevel(logging.DEBUG)

# Silence noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.getLogger("cerebras").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)

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
    os.getenv("GROQ_API_KEY3"),
    os.getenv("GROQ_API_KEY4"),
    os.getenv("GROQ_API_KEY5"),
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
    os.getenv("GEMINI_API_KEY4"),
    os.getenv("GEMINI_API_KEY5"),
    os.getenv("GEMINI_API_KEY6"),
    os.getenv("GEMINI_API_KEY7")
]

CEREBRAS_MODEL = [
    "llama3.1-8b", 
    "gpt-oss-120b"
]
CEREBRAS_KEYS = [
    os.getenv("CEREBRAS_API_KEY0"),
    os.getenv("CEREBRAS_API_KEY1"),
    os.getenv("CEREBRAS_API_KEY2"),
    os.getenv("CEREBRAS_API_KEY3"),
    os.getenv("CEREBRAS_API_KEY4"),
    os.getenv("CEREBRAS_API_KEY5")
]


# # Test each llm with API * MODEL
llm = LLMOrchestrator(
    groq={
        "groq_models" : GROQ_MODEL,
        "groq_keys" : GROQ_KEYS,
    },
    # gemini={
    #     "gemini_models" : GEMINI_MODEL,
    #     "gemini_keys" : GEMINI_KEYS,
    # },
    cerebras={
        "cerebras_models": CEREBRAS_MODEL,
        "cerebras_keys" : CEREBRAS_KEYS
    },
    debug=1,        # major logs
    verbose=1,      # in-depth trace
    prompt="You are a good chatbot",
    temperature=0.2,
    max_output_tokens=400,
    test_mode=1 # used to test each model * each api * each provider
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
#     cerebras={
#         "cerebras_models": CEREBRAS_MODEL,
#         "cerebras_keys" : CEREBRAS_KEYS
#     },
#     debug=True,        # major logs
#     verbose=True,      # in-depth trace
#     prompt="You are a good chatbot",
#     temperature=0.2,
#     max_output_tokens=400,
# )


# print(llm.call("What is the only thing that makes a programmers happy?"))
# print(llm.call("Divided by nations, united by coding"))

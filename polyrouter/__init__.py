# goal -> keep it simple and light weight
# initialise the public scope classes which users can access
# metadata for the library

from .LLMOrchestrator import LLMOrchestrator

from .Exceptions import (
    AllModelsFailedError,
    AllClientsExhaustedError,
    ModelRateLimit,
    InvalidAPIKey,
    UnknownError, 
    NoModelMentioned, 
    NoAPIKeysError,
    InvalidJSONResponseError
)


# Package Metadata
__version__ = "0.1.0"
__author__ = "Pratham Tomar"



# if something is not defines in __all__ it means that class is private for the users
# instead of from polyrouter.LLMOrchestrator import LLMOrchestrator -> polyrouter import LLMOrchestrator
__all__ = [
    "LLMOrchestrator",
    "AllModelsFailedError",
    "AllClientsExhaustedError",
    "ModelRateLimit",
    "InvalidAPIKey",
    "UnknownError", 
    "NoModelMentioned", 
    "NoAPIKeysError",
    "InvalidJSONResponseError"
]
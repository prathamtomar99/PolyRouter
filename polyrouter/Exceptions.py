# this file will be responsible for defination of all the user defined Exceptions
import logging

logger = logging.getLogger(__name__)

class LLMError(Exception):
    def __init__(self, message):
        logger.error(message)
        super().__init__(message)


class AllModelsFailedError(LLMError):
    def __init__(self, message):
        super().__init__(message)


class ModelRateLimit(LLMError):
    def __init__(self, message):
        super().__init__(message)


class AllClientsExhaustedError(LLMError):
    def __init__(self, message):
        super().__init__(message)


class InvalidAPIKey(LLMError):
    def __init__(self, message):
        super().__init__(message)


class InvalidJSONResponseError(LLMError):
    def __init__(self, message):
        super().__init__(message)


class NoAPIKeysError(LLMError):
    def __init__(self,message):
        super().__init__(message)


class NoModelMentioned(LLMError):
    def __init__(self,message):
        super().__init__(message)


class UnknownError(LLMError):
    def __init__(self,message):
        super().__init__(message)